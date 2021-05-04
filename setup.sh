mkdir -p ~/.streamlit
echo "[server]
headless = true
port = $PORT
enableCORS = false

[theme]
primaryColor='#FF7733'
backgroundColor='#999999'
secondaryBackgroundColor='#F0F2F6'
textColor='#262730'
font='sans serif'
" > ~/.streamlit/config.toml

#sed -i '57s/False/True/' $(python -c 'import streamlit; print(streamlit.elements.file_uploader.__file__)')
