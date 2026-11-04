"""reel-tool savereel: builds the iPhone Shortcut "SaveReel" that the upload page's "To gallery" button runs (maintainers).

    reel-tool savereel build [DIR]     unsigned SaveReel.<lang>.shortcut files (en, ru, pl) into DIR (default: the data dir)
    reel-tool savereel sign DIR        macOS only: signs them for anyone (shortcuts sign --mode anyone) into upload-page/shortcut/
    reel-tool savereel check FILE      prints what a signed file carries (signer certificates), for the privacy check

The page opens shortcuts://run-shortcut?name=SaveReel&input=text&text=<address of the video>. The shortcut:
    If Shortcut Input has any value: Get Contents of URL (Shortcut Input), Save to Photo Album
    Otherwise: a short alert (opened by hand, without a video) in the page's language
iOS imports only signed files; signing needs a Mac signed in to an Apple ID. The page serves the signed copies at
/shortcut/<lang>/SaveReel.shortcut, so the file name (= the shortcut's name on import) is always SaveReel.
Privacy: an "anyone" signature carries only Apple's certificate chain, whose leaf has a random ID that changes with every
signature (no name, email, Apple ID or phone number); run `check` on every new file anyway before it goes into git.
The leaf certificate is valid for about 13 months (`check` prints the date): sign again before it runs out.
"""
import plistlib, subprocess, sys, uuid
from pathlib import Path

import common as C

NAME = "SaveReel"
OUT = C.ROOT / "upload-page" / "shortcut"
ALERT = {"en": "Open a finished Reel on the Reel Studio page and tap To gallery.",
         "ru": "Откройте страницу Reel Studio и нажмите «В галерею» у готового видео.",
         "pl": "Otwórz stronę Reel Studio i stuknij „Do galerii” przy gotowym filmie."}


def action(ident, **params):
    return {"WFWorkflowActionIdentifier": ident, "WFWorkflowActionParameters": params}


def workflow(lang):
    group, fetch = str(uuid.uuid4()).upper(), str(uuid.uuid4()).upper()
    shortcut_input = {"Type": "ExtensionInput"}
    branch = lambda mode, **p: action("is.workflow.actions.conditional", GroupingIdentifier=group, WFControlFlowMode=mode, **p)
    actions = [
        branch(0, WFCondition=100,                                          # 100 = "has any value"
               WFInput={"Type": "Variable", "Variable": {"Value": shortcut_input, "WFSerializationType": "WFTextTokenAttachment"}}),
        action("is.workflow.actions.downloadurl", UUID=fetch, WFHTTPMethod="GET", ShowHeaders=False,
               WFURL={"Value": {"string": "￼", "attachmentsByRange": {"{0, 1}": shortcut_input}}, "WFSerializationType": "WFTextTokenString"}),
        action("is.workflow.actions.savetocameraroll",
               WFInput={"Value": {"OutputUUID": fetch, "Type": "ActionOutput", "OutputName": "Contents of URL"},
                        "WFSerializationType": "WFTextTokenAttachment"}),
        branch(1),                                                          # Otherwise
        action("is.workflow.actions.alert", WFAlertActionTitle=NAME, WFAlertActionMessage=ALERT[lang], WFAlertActionCancelButtonShown=False),
        branch(2, UUID=str(uuid.uuid4()).upper()),                          # End If
    ]
    return {"WFWorkflowName": NAME, "WFWorkflowActions": actions,
            "WFWorkflowClientVersion": "2605.0.5", "WFWorkflowMinimumClientVersion": 900, "WFWorkflowMinimumClientVersionString": "900",
            "WFWorkflowIcon": {"WFWorkflowIconStartColor": 4282601983, "WFWorkflowIconGlyphNumber": 61440},
            "WFWorkflowInputContentItemClasses": ["WFStringContentItem", "WFURLContentItem"],
            "WFWorkflowHasShortcutInputVariables": True, "WFWorkflowTypes": [], "WFQuickActionSurfaces": [],
            "WFWorkflowOutputContentItemClasses": [], "WFWorkflowHasOutputFallback": False, "WFWorkflowImportQuestions": []}


def build(folder):
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    for lang in ALERT:
        p = folder / f"{NAME}.{lang}.shortcut"
        p.write_bytes(plistlib.dumps(workflow(lang), fmt=plistlib.FMT_BINARY))
        print("built", p)


def sign(folder):
    if not C.IS_MAC:
        C.fail("signing needs macOS (the shortcuts command); copy the folder to a Mac and run: reel-tool savereel sign DIR")
    OUT.mkdir(parents=True, exist_ok=True)
    for lang in ALERT:
        src, dst = Path(folder) / f"{NAME}.{lang}.shortcut", OUT / lang / f"{NAME}.shortcut"
        dst.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["shortcuts", "sign", "--mode", "anyone", "--input", str(src), "--output", str(dst)], capture_output=True, text=True)
        if r.returncode or not dst.exists():
            C.fail(f"shortcuts sign failed for {lang}: {(r.stderr or r.stdout).strip()}")
        print("signed", dst, f"({dst.stat().st_size} bytes)")


def check(path):
    """the signed file is Apple Encrypted Archive: header, then a plist of auth data with the signer's certificate chain"""
    b = Path(path).read_bytes()
    if b[:4] != b"AEA1":
        C.fail("not a signed shortcut (no AEA1 header)")
    n = int.from_bytes(b[8:12], "little")
    auth = plistlib.loads(b[12:12 + n])
    print("auth data keys:", ", ".join(sorted(auth)))
    try:
        from cryptography import x509
    except ImportError:
        x509 = None
    for i, der in enumerate(auth.get("SigningCertificateChain", [])):
        if x509:
            c = x509.load_der_x509_certificate(der)
            print(f"cert {i}: subject={c.subject.rfc4514_string()}  issuer={c.issuer.rfc4514_string()}  until {c.not_valid_after_utc:%Y-%m-%d}")
            for e in c.extensions:
                print(f"    ext {e.oid.dotted_string} {getattr(e.oid, '_name', '')}: {str(e.value)[:160]}")
        else:
            print(f"cert {i}: {len(der)} bytes (install cryptography to decode)")
    for k, v in auth.items():
        if k != "SigningCertificateChain":
            print(f"{k}: {type(v).__name__} {len(v) if hasattr(v, '__len__') else v}")


def main(argv):
    if not argv or argv[0] not in ("build", "sign", "check"):
        print(__doc__); return
    if argv[0] == "build":
        build(argv[1] if len(argv) > 1 else C.DATA / "savereel")
    elif argv[0] == "sign":
        sign(argv[1] if len(argv) > 1 else C.DATA / "savereel")
    else:
        check(argv[1])


if __name__ == "__main__":
    main(sys.argv[1:])
