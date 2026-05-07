#!/usr/bin/env bash
# Build the final Group43_report.pdf for Blackboard submission.
#
# Behaviour:
#   - If report_tex/veriguide.pdf exists  -> compile WITH signed receipt
#                                            and write Group43_report.pdf
#                                            to the project root.
#   - If report_tex/veriguide.pdf missing -> abort with a hint.
#
# The in-git copy at report_tex/Group43_report.pdf is reverted to the
# placeholder version after compilation, so a future `git push` never
# leaks the signed receipt to the public repository.
#
# Requires: tectonic (or pdflatex) on PATH.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
TEXDIR="$ROOT/report_tex"
RECEIPT="$TEXDIR/veriguide.pdf"
GIT_COPY="$TEXDIR/Group43_report.pdf"
FINAL_PDF="$ROOT/Group43_report.pdf"

# ---- Locate a TeX engine -------------------------------------------
if command -v tectonic >/dev/null 2>&1; then
    TEX_CMD=(tectonic --keep-logs "$TEXDIR/Group43_report.tex")
elif [[ -x /tmp/tectonic/tectonic ]]; then
    TEX_CMD=(/tmp/tectonic/tectonic --keep-logs "$TEXDIR/Group43_report.tex")
elif command -v latexmk >/dev/null 2>&1; then
    TEX_CMD=(latexmk -pdf -outdir="$TEXDIR" "$TEXDIR/Group43_report.tex")
elif command -v pdflatex >/dev/null 2>&1; then
    TEX_CMD=(pdflatex -output-directory "$TEXDIR" "$TEXDIR/Group43_report.tex")
else
    echo "ERROR: no TeX engine found (tectonic / latexmk / pdflatex)" >&2
    exit 1
fi

# ---- Sanity check the signed receipt -------------------------------
if [[ ! -f "$RECEIPT" ]]; then
    cat <<EOF >&2
ERROR: $RECEIPT not found.

The final report needs a signed VeriGuide receipt. Sign 4610067.pdf
in macOS Preview (or any PDF tool), then save it as:

    $RECEIPT

After that, re-run this script.
EOF
    exit 1
fi

echo "[build] using receipt: $RECEIPT"
echo "[build] running:       ${TEX_CMD[*]}"

# ---- Compile -------------------------------------------------------
"${TEX_CMD[@]}" >"$ROOT/build.log" 2>&1 || {
    echo "ERROR: TeX compile failed; see $ROOT/build.log" >&2
    tail -25 "$ROOT/build.log" >&2
    exit 1
}

# ---- Move the freshly compiled PDF to project root -----------------
cp "$GIT_COPY" "$FINAL_PDF"
echo "[build] wrote $FINAL_PDF ($(du -h "$FINAL_PDF" | awk '{print $1}'))"

# ---- Revert the in-git copy so GitHub stays clean ------------------
if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    if git -C "$ROOT" diff --quiet HEAD -- report_tex/Group43_report.pdf; then
        echo "[build] in-git copy already matches HEAD"
    else
        git -C "$ROOT" checkout HEAD -- report_tex/Group43_report.pdf
        echo "[build] reverted report_tex/Group43_report.pdf to placeholder"
    fi
fi

echo "[build] done. Upload $FINAL_PDF to Blackboard."
