mkdir -p ~/.streamlit
echo "[server]
headless = true
port = $PORT
enableCORS = false
" > ~/.streamlit/config.toml

sed -i '57s/False/True/' $(python -c 'import streamlit; print(streamlit.FileUploaderMixin.__file__)')
