# Instrukcja uruchomienia kodu

Skrypt działa w Python 3.12.3 i wyższych.

W konsoli należy wykonać polecenie:

```bash
pip install -r requirements.txt
```

Polecenie to zainstaluje wszystkie zależności wymagane do uruchomienia projektu.

## Wykorzystane biblioteki

* **ifcopenshell** – biblioteka służąca do odczytu, tworzenia i modyfikowania plików IFC oraz pracy z ich strukturą i geometrią.
* **numpy** – biblioteka do wykonywania obliczeń numerycznych oraz operacji na tablicach i wektorach.
* **shapely** – biblioteka do wykonywania operacji geometrycznych na obiektach 2D, takich jak punkty, linie i wielokąty.
* **pathlib** – biblioteka ułatwiająca zarządzanie ścieżkami plików i katalogów.
* **shutil** – biblioteka umożliwiająca wykonywanie operacji na plikach i katalogach, takich jak kopiowanie i przenoszenie.
* **matplotlib** – biblioteka służąca do tworzenia wykresów i wizualizacji danych.

## Opis stworzonych plików

* **README.md** – opis projektu oraz instrukcja jego uruchomienia.
* **requirements.txt** – plik zawierający informacje o bibliotekach wymaganych do uruchomienia projektu.
* **Walidacja.py** – skrypt służący do walidacji plików IFC poprzez sprawdzanie poprawności ich struktury, brakujących i zduplikowanych atrybutów, przypisania elementów do poziomów oraz zawartości zestawów właściwości (PSET).
* **Tools.py** – plik zawierający klasę `IFCValidator`, wykorzystywaną przez skrypt `Walidacja.py` do przeprowadzania dodatkowych kontroli plików IFC.
* **Wstawienie.py** – skrypt służący do wstawiania anteny z pliku `ANTENA.ifc` do pliku `SEGMENT.ifc` na określonej wysokości i pod określonym azymutem. Skrypt automatycznie wybiera odpowiednią nogę segmentu, a następnie wyznacza punkt wstawienia poprzez przecięcie geometrii nogi z płaszczyzną na wybranej wysokości i wyznaczenie centroidu powstałego przekroju. Na tej podstawie antena jest umieszczana w odpowiednim miejscu oraz orientowana zgodnie z zadanym azymutem. Zapisuje kopie oryginalnych plików w folderze "wynik".
* **Wykres.py** – pomocniczy skrypt służący do wizualizacji przykładowego procesu wstawiania anteny.
* **Zadanie rekrutacyjne.rfa** – rodzina stworzona na drugie zadanie

## Weryfikacja poprawności pliku ANTENA.ifc

W wyniku przeprowadzonej walidacji stwierdzono:

* niepotrzebny `IfcBuildingStorey` (Level 2).

## Weryfikacja poprawności pliku SEGMENT.ifc

W wyniku przeprowadzonej walidacji stwierdzono:

* niekonsekwentne przypisanie poziomu (`Level`) dla elementu o GUID: `2DvXx2IVX2MQj$01oZeQ2B`,
* śruby nie posiadają przypisanych nazw,
* w pliku znajduje się relacja materiałowa na pozycji `#22526`, która nie jest przypisana do żadnego elementu.

## Property Sety

W pliku `SEGMENT.ifc` znajduje się wiele zestawów właściwości (Property Set), zarówno przypisanych automatycznie podczas eksportu, jak i prawdopodobnie wyeksportowanych celowo przez dostawcę rodziny. W pliku znajduje się również `Pset_SkySnap`, który zawiera istotne właściwości elementów modelu.

Zawartość Property Setów obejmuje parametry, których można oczekiwać w przypadku tego typu konstrukcji. Ich szczegółowa zawartość zależy od informacji zawartych w modelu oraz od danych zdefiniowanych przez autora modelu, dlatego nie wymaga ona dodatkowego komentarza w ramach niniejszego projektu.

W pliku `ANTENA.ifc` znajduje się znacznie mniej Property Setów. Jednym z istotniejszych jest `Pset_SkySnap`.
