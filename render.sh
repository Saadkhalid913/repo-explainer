#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./render.sh <input_dir> [-o|--output <output_dir>]

Examples:
  ./render.sh kubernetes-docs-v2 -o kubernetes-docs
  ./render.sh /abs/path/to/docs -o /abs/path/to/site
EOF
}

input_dir=""
output_dir=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      output_dir="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      if [[ -z "$input_dir" ]]; then
        input_dir="$1"
        shift
      else
        echo "Unexpected argument: $1" >&2
        usage >&2
        exit 1
      fi
      ;;
  esac
done

if [[ -z "$input_dir" ]]; then
  echo "Missing input_dir." >&2
  usage >&2
  exit 1
fi

input_dir="${input_dir%/}"
if [[ -z "$output_dir" ]]; then
  output_dir="${input_dir}/site"
fi

if [[ ! -d "$input_dir" ]]; then
  echo "Input directory not found: $input_dir" >&2
  exit 1
fi

if ! command -v mkdocs >/dev/null 2>&1; then
  echo "mkdocs not found. Install with: python3 -m pip install mkdocs" >&2
  exit 1
fi

tmp_dir="$(mktemp -d)"
cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

input_dir="$(cd "$input_dir" && pwd)"

if command -v realpath >/dev/null 2>&1 && [[ -d "$output_dir" ]]; then
  output_dir="$(realpath "$output_dir")"
else
  output_dir="$(cd "$(dirname "$output_dir")" && pwd)/$(basename "$output_dir")"
fi

mkdir -p "$output_dir"

config_file="$tmp_dir/mkdocs.yml"
cat > "$config_file" <<EOF
site_name: "$(basename "$input_dir")"
docs_dir: "$input_dir"
site_dir: "$output_dir"
use_directory_urls: false
EOF

mkdocs build -f "$config_file" --clean
echo "Built site at: $output_dir"
