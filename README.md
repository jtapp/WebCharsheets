# web-charsheets

Web-charsheets is a lightweight tool to edit and share character sheets between a small group of players.

## Requirements

To run the webapp, all you need is a `bash` installed and a python3 on your path that includes the `pip`, `venv`, and `sqlite3` modules.

The utility scripts are written to require `imagemagick`, `pdftoppm` (from the Debian `poppler-utils` package), `jq`, and a `base64` util - but it should be relatively straightforward to use platform-specific or online tools to achieve the same functionality as needed.

## How it works

For each TTRPG you want to play, you provide a character sheet PDF, and JSON markup of where to position input fields over the template.

Once you give that data to `web-charsheets`, you can start creating and editing new instances of your template straight from the homepage.

After a new sheet instance, you'll be taken to the "charsheet" page. At the top, you'll see the sheet's name, a "Save" button, a "Save as new..." button (to make a diverging copy of an existing sheet), and a "See history" button to see old versions of the sheet. There's also a toggle to turn "Edit Mode" off, which converts input fields to rendered text, and will also display b64-encoded PNG URIs on their own line as embedded images (useful for displaying character art and symbols). 

The "charsheet" page renders a PNG version of the character sheet, and then places `<input>` and `<textarea>` tags over that image using relative coordinates. Currently, only `type="text"` elements are supported, but this works surprisingly well! ...though it may change in the future. The frontend uses hardcoded pixel cutoffs to adjust input field font sizes and convert `<input>`s to `<textarea>`s.

## Adding Charsheet Types

Adding new character sheet types to the app is currently a manual process with several steps. It's admittedly a rough edge. Fortunately, each step has a utility script to help you out:

 1. Convert your character sheet PDF to a PNG using `util/pdf2png.sh`.
 2. (Recommended) Open that PNG with [anylabeling](https://github.com/vietanhdev/anylabeling) and create a JSON markup, with named rectangles describing your input fields that you want to be available on the character sheet.
 3. Convert your anylabelling JSON file with `anylab2form_parts.sh`. (Alternatively: BYO JSON file generated any way you like that matches `form_parts_schema` in `src/models.py`.)
 4. Encode your png image to a text file using `img2b64.sh`.
 5. If you haven't already done so, launch the `web-charsheets` server via either `run*.sh` script to generate the database file. You can kill the app immediately after it finishes startup. The db file will typically be made under `src/instances/web-charsheets.db`.
 6. Activate your venv, cd to `util/`, kill your `web-charsheets` server (if active), and run:
  
`python load_charsheet_type.py <template_name> <converted_json_path> <b64_image_path> <path_to_db_file>`

 7. Relaunch the server and start creating new instances of your character sheet type from the app's homepage.

## Deployment

Clone repo; run script.
```
git clone <repo_url>
cd web-charsheets/
chmod +x run-prod.sh
./run-prod.sh
```

Reverse-proxy using web server of your choosing, and gate with basic auth. Caddyfile example:
```
charsheets.example.com {
    basicauth {
        dnd_club JhJDE0JDFSTGtaQJDVVsaXpid0scHZhZy9KWUNt
    }
    reverse_proxy localhost:7420
}
```
