# .github/workflows/update-token.yml
name: Auto Update Mediabay Token

on:
  schedule:
    - cron: '0 */6 * * *'  # Har 6 soatda
  workflow_dispatch:  # Qo'lda ishga tushirish

jobs:
  update-token:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install requests selenium webdriver-manager
      
      - name: Install Chrome
        run: |
          wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
          sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
          sudo apt-get update
          sudo apt-get install -y google-chrome-stable
      
      - name: Get token and update Worker
        env:
          MEDIABAY_LOGIN: ${{ secrets.MEDIABAY_LOGIN }}
          MEDIABAY_PASSWORD: ${{ secrets.MEDIABAY_PASSWORD }}
          CF_API_TOKEN: ${{ secrets.CF_API_TOKEN }}
          CF_ACCOUNT_ID: ${{ secrets.CF_ACCOUNT_ID }}
          WORKER_NAME: ${{ secrets.WORKER_NAME }}
        run: python update_token_selenium.py
