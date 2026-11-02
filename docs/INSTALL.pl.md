# Reel Studio: instalacja

Reel Studio zamienia surowe nagrania, na których mówisz do kamery, w gotowe rolki na Instagram. Wycina powtórki i pauzy, czyści głos, dodaje napisy zsynchronizowane ze słowami, rysuje animacje do Twojego tekstu i sprawdza wynik, zanim go odda. Działa w Claude Code.

## Czego potrzebujesz

- Planu Claude z dostępem do Claude Code (Pro albo Max) i Claude Code w terminalu (polecenie `claude`)
- Jednego z tych komputerów:
  - Windows 10 lub 11 (64-bitowy) z Git for Windows
  - Linux na zwykłym PC: Ubuntu 22.04 lub 24.04 albo system na nich oparty (Zorin OS, Linux Mint)
  - Mac z procesorem Apple (M1 lub nowszy). Maki z Intelem nie są obsługiwane
- Około 10 GB wolnego miejsca na dysku
- Internetu przy pierwszej instalacji

Karta graficzna NVIDIA nie jest potrzebna. Jeśli ją masz, rozpoznawanie mowy działa mniej więcej 10 razy szybciej, a wynik jest taki sam.

## Ważne

Polecenie `/plugin` działa tylko w terminalu (w programie `claude`), nie w aplikacji Claude na komputer. Dlatego wtyczkę instalujesz z terminala. Potem możesz z niej korzystać także w aplikacji.

## Krok 1. Przygotowanie

**Windows.** Otwórz PowerShell i wpisz:

```powershell
winget install --id Git.Git -e
```

Potem zamknij terminal i otwórz go ponownie.

**Linux (Ubuntu, Zorin OS, Mint).** Otwórz terminal i wpisz:

```bash
sudo apt install -y git curl tar
```

**Mac.** Otwórz Terminal i wpisz:

```bash
xcode-select --install
```

Jeśli pojawi się okno, kliknij „Zainstaluj”. Jeśli system odpowie, że narzędzia już są, przejdź dalej.

## Krok 2. Instalacja wtyczki

W terminalu, po kolei:

```bash
claude plugin marketplace add SirOxygenFish/reel-studio
```

```bash
claude plugin install reel-studio@siroxygenfish
```

## Krok 3. Instalacja narzędzi

Uruchom Claude Code (w terminalu albo w aplikacji) i wpisz:

```
/reel-setup
```

Za pierwszym razem trwa to od 10 do 30 minut. Wszystko trafia do osobnego folderu wtyczki, system zostaje nietknięty i nie trzeba podawać hasła administratora. Gdy Claude zapyta o zgodę na `reel-tool`, wybierz „zawsze zezwalaj”.

## Krok 4. Sprawdzenie

```
/reel-doctor
```

Jeśli czegoś brakuje, doctor poda gotową linijkę do wklejenia w terminal. Na Linuksie to zwykle jedno polecenie `sudo apt install -y ...` z bibliotekami dla przeglądarki.

## Jak z tego korzystać

1. Wrzuć nagrania do folderu projektu.
2. Napisz do Claude: „zmontuj” albo `/reel`.
3. Gotowa rolka pojawi się w folderze `reels-done`.

Możesz doprecyzować: „tylko twarz, bez animacji”, „bez twarzy, same animacje”, „tytuł: ...”. Jeśli nagrasz poprawkę do gotowej rolki, napisz „to poprawka do ostatniej”: zostaje gotowy montaż, a podmieniają się tylko powtórzone zdania.

Więcej (po angielsku): [README](../README.md).
