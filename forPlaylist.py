import os

#you can use this one if you want to sort your music names
def change_names(folder_path):
    # Taking the list of files form the folder
    lista_plikow = os.listdir(folder_path)

    # Sorting
    lista_plikow.sort()

    # Searching
    for indeks, stary_nazwa_pliku in enumerate(lista_plikow):
        nowa_nazwa_pliku = f"{indeks + 1}{os.path.splitext(stary_nazwa_pliku)[1]}"
        stary_pelna_sciezka = os.path.join(folder_path, stary_nazwa_pliku)
        nowy_pelna_sciezka = os.path.join(folder_path, nowa_nazwa_pliku)

        # Renaming
        os.rename(stary_pelna_sciezka, nowy_pelna_sciezka)
        print(f'Zmieniono nazwę: {stary_nazwa_pliku} -> {nowa_nazwa_pliku}')

def create(folder_path):
    monke = os.listdir(folder_path)

    playlist = []

    for n in monke:
        # Name of the file withat folder_path 
        file_path = os.path.join(folder_path, n)
        playlist.append(file_path)
    
    return playlist
