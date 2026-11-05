# Tekst do instalacji (polski)

Skopiuj całą zawartość ramki poniżej i wklej ją do nowego czatu ustawionego tak jak w filmie 1 (karta Code, This computer, Twój nowy folder, Opus 5.5 z Effort High, Auto). Folder tego czatu stanie się Twoim folderem z filmami. Jedną linijkę pod koniec możesz zmienić przed wysłaniem.

```text
Zainstaluj, proszę, Reel Studio na tym komputerze. Nie znam się na technice: wszystko rób sam, przed każdym krokiem napisz krótko, co robisz, i rozmawiaj ze mną po polsku.

Zasady:
- Nie zmieniaj niczego, czego ta lista nie wymaga: żadnych ustawień systemu, innych programów ani plików poza wymienionymi tu folderami.
- Nigdy nie uruchamiaj niczego, co wymaga uprawnień administratora (sudo, okno Windows z prośbą o zgodę, „Uruchom jako administrator”). Jeśli taki krok jest potrzebny, pokaż mi dokładne polecenie, powiedz, gdzie je wkleić, i poczekaj, aż napiszę, że gotowe.
- Jeśli krok się nie uda, przeczytaj błąd, napraw go najprostszym sposobem i w jednym zdaniu napisz, co się stało.
- Ten czat zostaje moim codziennym czatem do Reel Studio, także z telefonu. Zapamiętaj, co tu skonfigurujesz: będę wracać do tego samego czatu z pytaniami (Tailscale, błędy, zmiany). Nigdy nie każ mi zaczynać nowej sesji.

1. Sprawdź komputer: system i jego wersję, rodzaj procesora, wolne miejsce na dysku i czy jest git. Wynik napisz w dwóch linijkach. Reel Studio działa na Windows 10 lub 11 (64-bitowym), na Macu z procesorem Apple (M1 lub nowszym) i na 64-bitowym Linuksie opartym na Ubuntu (Ubuntu 22.04/24.04, Zorin OS, Mint), potrzebuje około 10 GB wolnego miejsca. Jeśli komputer się nie nadaje, przerwij i wyjaśnij dlaczego.

2. Doinstaluj to, czego brakuje:
   - Windows bez Gita: pokaż mi polecenie  winget install --id Git.Git -e  (może poprosić o zgodę), poczekaj na mnie i działaj dalej.
   - Linux bez git, curl albo tar: pokaż mi  sudo apt install -y git curl tar  i poczekaj na mnie.
   - Mac bez narzędzi dla programistów: uruchom  xcode-select --install  (otworzy się okno, kliknę Zainstaluj) i poczekaj na mnie.

3. Jeśli polecenie claude nie działa w terminalu, zainstaluj Claude Code tylko dla tego użytkownika (bez uprawnień administratora):
   - Windows, w PowerShellu:  irm https://claude.ai/install.ps1 | iex
   - Mac albo Linux:  curl -fsSL https://claude.ai/install.sh | bash

4. Od razu zainstaluj wtyczkę, jeszcze przed długą instalacją (to kilka sekund):
   claude plugin marketplace add SirOxygenFish/reel-studio
   claude plugin install reel-studio@siroxygenfish
   Jeśli jest już zainstalowana, uruchom zamiast tego  claude plugin update reel-studio@siroxygenfish . Jeśli po tym kroku czat się uruchomi ponownie, po prostu kontynuuj od kroku 5.

5. Znajdź zainstalowaną kopię: najnowszy folder ~/.claude/plugins/cache/siroxygenfish/reel-studio/<wersja>. W kolejnych krokach używaj jej bin/reel-tool (w Windows w PowerShellu: bin\reel-tool.cmd) z pełną ścieżką. Uruchom  reel-tool setup  w tle: pobiera 5-8 GB i trwa od 10 do 30 minut. Co kilka minut napisz w jednej linijce, ile już zrobione. Gdy skończy, uruchom  reel-tool doctor  i napraw wszystko, co zgłosi (kroki z uprawnieniami administratora pokaż mi, jak wyżej).

6. Folder na filmy: folder, w którym otwarto ten czat (Twój bieżący folder roboczy), to mój folder z filmami. Pokaż mi jego pełną ścieżkę. Potem uruchom
   reel-tool autostart on --folder "<ten folder>"
   żeby strona wysyłania dla telefonu uruchamiała się sama przy każdym logowaniu. Autostart: [tak]  (jeśli zmienię to na nie, pomiń to polecenie i powiedz mi, że stronę można uruchomić ręcznie poleceniem  reel-tool phone-link --start ). Następnie uruchom  reel-tool shortcut on , żeby na pulpicie pojawiła się ikona, która uruchamia stronę i pokazuje link dla telefonu.

7. Uruchom  reel-tool phone-link --start --open . W odpowiedzi pokaż mi link dla telefonu i kod QR z wyniku polecenia (w bloku kodu) i napisz: skieruj na kod aparat iPhone'a, otwórz stronę w Safari, stuknij Udostępnij, a potem Do ekranu początkowego.

8. Powiedz mi:
   - Po instalacji mogę obniżyć Effort do Medium (menu modelu pod polem wiadomości), żeby oszczędzać limit.
   - Każde pytanie później, także o Tailscale, żeby korzystać z telefonu poza domem: zadaję w tym samym czacie.

9. Potem przepisz dosłownie tę ściągawkę:
   Na co dzień:
   1. iPhone: ikona Reel Studio, wybierz nagrania, Wyślij.
   2. Aplikacja Claude: Code, sesja mojego komputera (zawsze ten sam czat).
   3. Napisz: zmontuj (i czego jeszcze sobie życzysz).
   4. Poczekaj, aż Claude napisze, że gotowe.
   5. Strona wysyłania: Do galerii. Rolka jest w Zdjęciach.

10. Zakończ ostatnią wiadomość dokładnie tą linijką:
   Gotowe. Teraz wyślij w tym czacie /reload-plugins.
   (/reload-plugins włącza Reel Studio w tym samym czacie.) Jeśli później poproszę o rolkę, a nie widzisz umiejętności reel-studio, powiedz mi, żeby całkowicie zamknąć aplikację Claude i ponownie otworzyć ten sam czat; do tego czasu czytaj umiejętności w zainstalowanej kopii i uruchamiaj reel-tool z pełną ścieżką.

Niczego więcej nie ruszaj.
```
