from kaitaistruct import KaitaiStream
import io


from rekordbox_pdb import RekordboxPdb

file = "../../francois_local/export.pdb"

with open(file, "rb") as f:
    data = f.read()

    ks = KaitaiStream(io.BytesIO(data))
    pdb = RekordboxPdb(is_ext=False, _io=ks)

print("Chargement terminé ! 🎉")
print(type(pdb))


row = pdb.RowRef(1)


for pl in pdb:
    print(f"Playlist: {pl.name} ({len(pl.tracks)} morceaux)")

    for t in pl.tracks:
        print(f"   - {t.title} / {t.artist}")
