with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx_nasdaq = text.find('id="windowNasdaq"')
idx_crypto_notice = text.find('<div class="market-notice-banner banner-open">', idx_nasdaq)
end_crypto_notice = text.find('</div>', idx_crypto_notice) + 6
crypto_notice_html = text[idx_crypto_notice:end_crypto_notice]

text = text[:idx_nasdaq] + text[idx_nasdaq:text.find('<!--', idx_nasdaq)].replace('id="gridCrypto"', 'id="gridNasdaq"') + text[text.find('<!--', idx_nasdaq):]

idx_crypto = text.find('id="windowCrypto"')
idx_bist_notice = text.find('<div class="market-notice-banner banner-closed" id="bannerBistNotice">', idx_crypto)
end_bist_notice = text.find('</div>', idx_bist_notice) + 6
bist_notice_html = text[idx_bist_notice:end_bist_notice]

text = text[:idx_crypto] + text[idx_crypto:text.find('<!--', idx_crypto)].replace('id="gridBist"', 'id="gridCrypto"') + text[text.find('<!--', idx_crypto):]

idx_bist = text.find('id="windowBist"')
idx_nasdaq_notice = text.find('<div class="market-notice-banner banner-closed" id="bannerNasdaqNotice">', idx_bist)
end_nasdaq_notice = text.find('</div>', idx_nasdaq_notice) + 6
nasdaq_notice_html = text[idx_nasdaq_notice:end_nasdaq_notice]

text = text[:idx_bist] + text[idx_bist:text.find('</div>\n        </div>', idx_bist)].replace('id="gridNasdaq"', 'id="gridBist"') + text[text.find('</div>\n        </div>', idx_bist):]

text = text.replace(crypto_notice_html, 'REPLACE_ME_NASDAQ')
text = text.replace(bist_notice_html, 'REPLACE_ME_CRYPTO')
text = text.replace(nasdaq_notice_html, 'REPLACE_ME_BIST')

text = text.replace('REPLACE_ME_NASDAQ', nasdaq_notice_html)
text = text.replace('REPLACE_ME_CRYPTO', crypto_notice_html)
text = text.replace('REPLACE_ME_BIST', bist_notice_html)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed")
