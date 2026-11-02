-- I don't use them but Mixxx sometimes insist on creating some…

DELETE FROM cues
WHERE type = 6 OR type = 7;
VACUUM; -- noqa: PRS
ANALYZE; -- noqa: PRS
