# Reel Studio: od czego zacząć

Reel Studio zamienia nagrania z iPhone'a w gotowe rolki na Instagram. Wysyłasz nagrania z telefonu, piszesz do Claude jedno słowo, a gotowa rolka wraca do Zdjęć. Montaż odbywa się na Twoim komputerze. Na tej stronie jest wszystko, co robisz sam, raz i po kolei.

Inne języki: [English](START_HERE.md) · [Русский](START_HERE.ru.md)

## 1. Czego potrzebujesz

- Planu Claude **Pro albo Max**.
- Komputera z jednym z systemów:
  - Windows 10 lub 11 (64-bitowy)
  - Mac z procesorem Apple (M1 lub nowszy). Mac z procesorem Intel się nie nada.
  - Linux oparty na Ubuntu 22.04 lub 24.04 (na przykład Zorin OS albo Linux Mint)
- Około **10 GB** wolnego miejsca i internetu przy pierwszej instalacji.
- iPhone'a z aplikacją **Claude**, zalogowaną na to samo konto.

Pracę wykonuje komputer, więc kiedy wysyłasz nagrania, musi być włączony, a aplikacja Claude otwarta (może być zminimalizowana).

## 2. Na komputerze, jednorazowo

1. **Zainstaluj aplikację Claude** ze strony [claude.ai/download](https://claude.ai/download) i zaloguj się.
2. **Obejrzyj film 1** (40 sekund): [Polski](https://github.com/SirOxygenFish/reel-studio/raw/main/docs/tutorials/tutorial1-pc.pl.mp4) · [English](https://github.com/SirOxygenFish/reel-studio/raw/main/docs/tutorials/tutorial1-pc.en.mp4) · [Русский](https://github.com/SirOxygenFish/reel-studio/raw/main/docs/tutorials/tutorial1-pc.ru.mp4). Film otworzy się albo pobierze, wystarczy go włączyć.
3. **Dwa przełączniki.** W aplikacji: Twoje imię w lewym dolnym rogu, potem **Settings**, potem **Claude Code**, przewiń do **Remote Control**:
   - **Connect new sessions to Remote Control**: **włącz**
   - **Let your phone and claude.ai start sessions here**: zostaw **wyłączony**
   - **Keep this computer awake for Remote Control**: **włącz**

   Aplikacja Claude nie ma jeszcze polskiej wersji, dlatego nazwy ustawień są tu po angielsku, tak jak na ekranie.
4. **Instalacja.** Otwórz kartę **Code**, zacznij **New session** (folder dowolny), skopiuj cały [tekst do instalacji](INSTALL_PROMPT.pl.md) i wyślij go. Zanim Claude uruchomi polecenie, poprosi o zgodę: zgadzaj się. Jeśli pokaże polecenie, które wymaga hasła administratora, wklej je tam, gdzie wskaże, i napisz mu, kiedy będzie gotowe. Instalacja trwa od 10 do 30 minut.
5. **Folder z filmami.** Gdy Claude napisze, że skończył, zamknij tę sesję i zacznij **New session** w folderze z filmami, który poda (zwykle `Reels` w folderze Wideo, a na Macu w folderze Filmy). To będzie Twoja codzienna sesja, z której korzystasz z telefonu. Zostaw ją otwartą.

## 3. Na iPhonie, jednorazowo

1. **Otwórz stronę wysyłania.** Na koniec instalacji komputer pokazał kod QR (ikona **Reel Studio na telefon** na pulpicie pokaże go znowu). Skieruj na niego aparat iPhone'a i otwórz stronę w Safari. Telefon musi być w tej samej sieci Wi-Fi co komputer.
2. **Dodaj SaveReel.** Ten skrót zapisuje gotową rolkę w Zdjęciach. Na stronie stuknij **Zainstaluj SaveReel**. Safari zapyta, czy otworzyć plik w Skrótach: stuknij Otwórz, potem przycisk dodawania na dole i Gotowe. Gdy pierwszy raz stukniesz **Do galerii**, iPhone zapyta o dostęp: zezwól na stałe (przycisk Always Allow na angielskim iPhonie). Jeśli to nie zadziała, zajrzyj do ostatniej części tej strony.
3. **Dodaj stronę do ekranu początkowego.** Nadal w Safari stuknij Udostępnij, potem Do ekranu początkowego i Dodaj.
4. **Obejrzyj film 2**: na stronie wysyłania stuknij **Jak to działa**. Film odtwarza się z Twojego komputera, w języku strony.
5. **Instagram w najwyższej jakości.** W Instagramie otwórz profil, menu (trzy kreski), wpisz **jakość** w wyszukiwarce ustawień i włącz przesyłanie w najwyższej jakości (w angielskim Instagramie: Upload at highest quality), inaczej Instagram mocniej kompresuje rolki.

## 4. Opcjonalnie: poza domem

Strona wysyłania działa tylko w domu, w Twojej sieci Wi-Fi. Żeby korzystać z niej wszędzie, zainstaluj darmową aplikację **Tailscale** na komputerze i na iPhonie ([tailscale.com/download](https://tailscale.com/download)), zaloguj się na obu tym samym kontem i włącz ją. Wtedy ikona **Reel Studio na telefon** pokaże drugi kod QR, „poza domem”: jego też dodaj do ekranu początkowego.

## 5. Na co dzień

1. iPhone: ikona **Reel Studio**, wybierz nagrania, **Wyślij**.
2. Aplikacja Claude: **Code**, sesja Twojego komputera.
3. Napisz: **zmontuj** (i czego jeszcze sobie życzysz).
4. Poczekaj, aż Claude napisze, że gotowe.
5. Strona wysyłania: **Do galerii**. Rolka jest w Zdjęciach.

## Ostateczność: zbuduj SaveReel ręcznie

Tylko jeśli **Zainstaluj SaveReel** nie zadziałało.

1. Otwórz aplikację Skróty i stuknij **+**.
2. Dodaj akcję **Get Contents of URL** (na polskim iPhonie nazwa jest przetłumaczona, szukaj słowa „URL”) i w polu adresu wybierz **dane wejściowe skrótu**.
3. Dodaj akcję **Save to Photo Album** (szukaj słowa „album”).
4. Zmień nazwę skrótu dokładnie na **SaveReel**. Przy pierwszym uruchomieniu stuknij Pozwól.
