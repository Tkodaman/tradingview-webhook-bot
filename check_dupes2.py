with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
print("Number of <script> tags:", len(re.findall(r'<script', text)))
print("Number of <style> tags:", len(re.findall(r'<style', text)))
print("Number of <div class=\"panel-container\">:", len(re.findall(r'panel-container', text)))
print("Number of renderMarketGroup:", len(re.findall(r'renderMarketGroup', text)))
