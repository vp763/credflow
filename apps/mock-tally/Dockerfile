FROM python:3.11-slim

WORKDIR /app

RUN pip install flask flask-cors

COPY data/ /app/data/

COPY <<EOF /app/app.py
from flask import Flask, request, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

DATA_DIR = '/app/data'

@app.route('/', methods=['POST'])
def handle_tally_request():
    # Read the XML request body
    xml_data = request.get_data(as_text=True)
    print(f"Received Tally request: {xml_data[:500]}...")
    
    # Determine which response to return based on request content
    if 'List of Companies' in xml_data:
        return send_from_directory(DATA_DIR, 'response_company_list.xml', mimetype='text/xml')
    elif 'List of Ledgers' in xml_data:
        return send_from_directory(DATA_DIR, 'response_ledgers.xml', mimetype='text/xml')
    elif 'Day Book' in xml_data and 'Sales' in xml_data:
        return send_from_directory(DATA_DIR, 'response_sales_vouchers.xml', mimetype='text/xml')
    elif 'Day Book' in xml_data and 'Receipt' in xml_data:
        return send_from_directory(DATA_DIR, 'response_receipt_vouchers.xml', mimetype='text/xml')
    else:
        # Default response
        return send_from_directory(DATA_DIR, 'response_company_list.xml', mimetype='text/xml')

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090, debug=True)
EOF

EXPOSE 9090

CMD ["python", "app.py"]