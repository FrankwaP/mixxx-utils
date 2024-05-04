# Fixing Mixxx's Database

As mentionned in [this issue](https://github.com/mixxxdj/mixxx/issues/12328) several foreign key constraints defined in Mixxx's database are incorrect, and SQL Alchemy (Python's library) does not like it.

I fixed these quite easily using a GUI called "DB  Browser for SQlite" (`sqlitebrowser`). Here I take the example of the incorrect foreign key of the `cue` table:

- Select the table and click on "Modify a Table"

![modify the table](images/fix_mixxx_db_01.png)

- Enlarge the new window so you can see "Foreign keys", then double click on the foreign key you want to edit (here there's only one) and simply change the values (here from `library_old` to `library`)

![modify the foreign key](images/fix_mixxx_db_02.png)

Great! Now do it with the other constraints mentionned in [this issue](https://github.com/mixxxdj/mixxx/issues/12328).

To modify the default value of the `filetype` filed of the `library` table:  

1. Select the `library` table and click on "Modify a Table"
2. Find the row mentionning `filetype` and the "Default" column
3. Double click on the "?" then delete it to leave an empty field.

Done! Now you can activate the foreign key pragma, [which was disable as a quick and dirty fix](https://github.com/mixxxdj/mixxx/blob/main/tools/mixxxdb_cleanup.sql) (BTW if you use it you can now remove the `PRAGMA foreign_keys = OFF;` line):

1. Click on "Edit Pragma"  
2. Tick the "Foreign Keys" box

Now you can save and close the database. And from now you're life will be very slightly better. :-)
