import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# The CSS block ends with:
#        }
#    </style>
#</head>
#<body>

idx1 = text.find('</style>')
print("</style> at:", idx1)

idx2 = text.find('<body>')
print("<body> at:", idx2)

# Find the end of the garbage... wait, the garbage might be INSIDE the body?
