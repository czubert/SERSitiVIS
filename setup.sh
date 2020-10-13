mkdir -p ~/.streamlit
echo "[server]
headless = true
port = $PORT
enableCORS = false
" > ~/.streamlit/config.toml

sed -i '57s/False/True/' $(python -c 'import streamlit; print(streamlit.elements.file_uploader.__file__)')
