with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Find the last valid closing tags for the modal we inserted
idx_modal = text.find('<!-- Hızlı Pozisyon Aç Modal -->')
if idx_modal != -1:
    idx_end_modal = text.find('</div>\n    </div>', idx_modal)
    if idx_end_modal != -1:
        # 16 is length of '</div>\n    </div>'
        end_of_content = idx_end_modal + 16
        
        # Keep everything up to the end of our modal, then add </body></html>
        cleaned_text = text[:end_of_content] + '\n\n</body>\n</html>\n'
        
        with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        print("Cleaned up dashboard.html")
