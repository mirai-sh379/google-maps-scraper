# Google Maps Extractor

Scrapes business listings from Google Maps and saves them to CSV. Uses [Camoufox](https://camoufox.com/) for anti-detection browsing.

## Extracted Data

| Field       | Description         |
|-------------|---------------------|
| name        | Business name       |
| rating      | Star rating         |
| reviews     | Number of reviews   |
| category    | Business category   |
| address     | Street address      |
| phone       | Phone number        |
| website     | Website URL         |
| hours       | Working hours       |
| price_level | Price level         |
| plus_code   | Google Plus Code    |

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager

## Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/google-maps-extractor.git
cd google-maps-extractor
```

2. Install dependencies:

```bash
uv sync
```

3. Install the Camoufox browser:

```bash
python -m camoufox fetch
```

4. Create `.env` file:

```bash
cp .env.example .env
```

## Configuration

Edit `.env` to set defaults:

```env
SEARCH_QUERY=restaurants in New York
HEADLESS=true
LOG_LEVEL=DEBUG
```

## Usage

Run with defaults from `.env`:

```bash
uv run app/main.py
```

Override via CLI arguments:

```bash
uv run app/main.py -q "cafes in London" --no-headless --log-level INFO
```

### CLI Arguments

| Argument       | Description                  | Default              |
|----------------|------------------------------|----------------------|
| `-q, --query`  | Search query                 | from `.env`          |
| `--headless`   | Run browser in headless mode | `true`               |
| `--no-headless`| Show browser window          | -                    |
| `--log-level`  | DEBUG, INFO, WARNING, ERROR  | `DEBUG`              |

## Output

Results are saved to `app/data/<query>.csv`, e.g.:

```
app/data/restaurants_in_new_york.csv
app/data/cafes_in_london.csv
```
