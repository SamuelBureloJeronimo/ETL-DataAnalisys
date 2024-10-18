import os
from flask import Flask, current_app, flash, render_template, request, redirect, make_response, url_for
import pandas as pd

app = Flask(__name__);
# Configurar la carpeta de subida
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.secret_key = 'supersecretkey'

@app.route('/')
def index():
    return render_template('index.html');

@app.route('/limpiar-txt')
def limpiar_txt():
    # Ruta del archivo TXT
    file_path_txt = request.cookies.get('file_path_txt')

    # Leer el archivo de texto y cargarlo en un DataFrame
    df = pd.read_csv(file_path_txt, delimiter='|')
    
    # Limpiar el DataFrame
    df.columns = df.columns.str.strip()
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    
    # Convertir el DataFrame a HTML
    tabla_html = df.to_html(classes='table table-striped', index=False)
    
    # Renderizar la tabla en una plantilla HTML
    return render_template('tabla.html', tabla=tabla_html)

@app.route('/preview')
def preview():
    # Obtener rutas de los archivos desde las cookies
    file_path_csv = request.cookies.get('file_path_csv')  # Ruta del archivo CSV
    file_path_xlsx = request.cookies.get('file_path_xlsx')  # Ruta del archivo XLSX
    file_path_txt = request.cookies.get('file_path_txt')  # Ruta del archivo TXT

    # Inicializar variables para los DataFrames
    df_csv, df_xlsx, df_text = None, None, None

    # Verificar si las rutas están presentes antes de leer los archivos
    if file_path_csv:
        try:
            df_csv = pd.read_csv(file_path_csv)  # Leer el archivo CSV
        except Exception as e:
            flash(f'Error al leer el archivo CSV: {str(e)}')
    
    if file_path_xlsx:
        try:
            df_xlsx = pd.read_excel(file_path_xlsx)  # Leer el archivo XLSX
        except Exception as e:
            flash(f'Error al leer el archivo XLSX: {str(e)}')
    
    if file_path_txt:
        try:
            df_text = pd.read_csv(file_path_txt, delimiter='|')  # Leer el archivo TXT con tabulaciones
        except Exception as e:
            flash(f'Error al leer el archivo TXT: {str(e)}')

    # Preparar contexto para la plantilla, enviando solo los DataFrames que no son None
    context = {
        'df_csv': df_csv,
        'df_xlsx': df_xlsx,
        'df_text': df_text
    }

    return render_template('preview.html', **context)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Crear una respuesta
        response = make_response(redirect('/preview'))

        # Verificar si se subieron archivos
        if 'files' not in request.files:
            flash('No se seleccionaron archivos')
            return redirect('/')
        
        files = request.files.getlist('files')
        
        # Si no se seleccionaron archivos, mostrar mensaje
        if len(files) == 0 or files[0].filename == '':
            flash('No se seleccionaron archivos')
            return redirect('/')

        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename):  # Verificar si el archivo tiene una extensión permitida
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)  # Guardar cada archivo en la carpeta de uploads
                
                # Establecer la cookie
                response.set_cookie('file_path_'+file.filename.rsplit('.', 1)[1].lower(), 'uploads/'+file.filename)
                uploaded_files.append(file.filename)
        
        if uploaded_files:
            flash(f'Archivos subidos correctamente: {", ".join(uploaded_files)}')
        else:
            flash('No se subieron archivos válidos')
        
    return response;




ALLOWED_EXTENSIONS = {'csv', 'txt', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_file(file, filename):
    """Procesa el archivo dependiendo de su extensión y devuelve un dataframe"""
    file_ext = filename.rsplit('.', 1)[1].lower()
    if file_ext == 'csv':
        df = pd.read_csv(file)  # Lee archivos CSV
    elif file_ext == 'txt':
        df = pd.read_csv(file, delimiter='\t')  # Lee archivos TXT con tabulador
    elif file_ext == 'xlsx':
        df = pd.read_excel(file)  # Lee archivos XLSX usando pandas
    else:
        raise ValueError("Tipo de archivo no soportado")
    
    return df