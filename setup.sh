mkdir -p ~/.streamlit
echo "[server]
headless = true
port = $PORT
enableCORS = false
" > ~/.streamlit/config.toml

sed -i '2125s/False/True/' $(python -c 'import streamlit; print(streamlit.DeltaGenerator.__file__)')
