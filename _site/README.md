# ChromeBird AI Labs Website

This website is built with HTML/CSS and Jekyll for component management (header/footer).
It is hosted on GitHub Pages.

## Local Development (Testing)

To test the site locally and see the `_includes` working (header/footer), you need to run Jekyll.
You can use the standard Ruby environment or Docker.

### Option 1: Using Docker (Recommended, No Install Mess)

Run the following command in the root of the repo:

```bash
docker run --rm --volume="$PWD:/srv/jekyll" --publish 4000:4000 jekyll/jekyll:3.8 jekyll serve
```

Then open `http://localhost:4000` in your browser.

### Option 2: Using Ruby/Gem

1.  Ensure you have Ruby installed.
2.  Install Jekyll: `gem install jekyll bundler`
3.  Run the server: `jekyll serve`
4.  Open `http://localhost:4000`.

## Structure

*   `_includes/`: Contains reusable HTML components (header).
*   `_config.yml`: Jekyll configuration.
*   `*.html`: Page files (must contain Front Matter `---` at the top to be processed).

## Deployment

Simply push to the main branch. GitHub Pages will automatically build the Jekyll site.
