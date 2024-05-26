# Suggestions to use these script

## Linux Terminal

```bash
script_name=mixxxdb_cleanup.sql  # change it to the desired script

database="${HOME}/.mixxx/mixxxdb.sqlite"
bakup_name="${HOME}/.mixxx/mixxxdb.sqlite.bak.$(date +%y%m%d%H%M)"
cp "$database" "$bakup_name"
sqlite3  "$database"  < "$script_name"
```

## GUI (Linux/Windows/macOS)

I presonnaly use "[DB brower for SQLite](https://sqlitebrowser.org/)" aka `sqlitebrowser`. Open the database then go to "Execute SQL" and copy paste the commands of the script.
