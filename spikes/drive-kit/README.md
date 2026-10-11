# aidist-spike: Google Drive connector test

Instructions for the agent. Do every step and report the results in one table at the end.
Don't fix or retry anything silently; the point is to see exactly what the connector does.

1. Using the Google Drive connector, find the folder `aidist-spike` (the folder that contains this README). List its files with their IDs, MIME types and sizes.
2. For each of `tricky.py`, `tricky.md`, `tricky.json`, `crlf.txt`, `large.py`:
   a. Fetch it with `read_file_content` and write the content, unchanged, to `~/aidist-s1/read/<name>`.
   b. Fetch it with `download_file_content`. Describe exactly what that tool returned (did it save a local file? return base64? return text? where?) and save the result to `~/aidist-s1/download/<name>`.
3. Run `shasum -a 256 ~/aidist-s1/read/* ~/aidist-s1/download/*` (on Windows: `certutil -hashfile <file> SHA256`). Mark each file MATCH or MISMATCH against:

   ```text
   0517f81d7097048ea6c21c23beff20397d40abea522048454d5b98d34805f025  tricky.py
   c915dc92773e5073abd0499ebc3f4aa0c9ae53ae37c88cd01569dcd4276a8867  tricky.md
   2c8e28200df1cdd7d54f043e7fbadc4de413c076eeba26cd5132582b6691d09c  tricky.json
   1fd4bdcae242cd3f84c1546575d3df80e44ca5516edfb536f3a6ffa42ba20675  crlf.txt
   8bf04172acdf845ca83c71a48f96af184385646c08449c525416c57bddc54307  large.py
   ```

4. For any MISMATCH, show the first line that differs between the expected content and what the connector returned.
5. Write test: with `create_file`, create `write-test.py` in the same folder containing exactly two lines: a tab followed by `print('שלום')`, then `x = 1` followed by three spaces. Then use `update_file` to add a third line `y = 2`. Read it back and report whether it matches byte for byte.
6. Report which app you're running in (Claude Desktop, Claude Code, Claude Science, Cursor), the OS, how long the run took, and roughly how many tokens the file transfers used.
