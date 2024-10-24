import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'secret_key'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'txt'}

# Función para verificar si el archivo tiene una extensión permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Función para cargar los archivos
def load_file(filepath):
    ext = filepath.rsplit('.', 1)[1].lower()
    if ext == 'csv':
        return pd.read_csv(filepath)
    elif ext == 'xlsx':
        return pd.read_excel(filepath)
    elif ext == 'txt':
        return pd.read_csv(filepath, delimiter='|')
    else:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    
    # Verificar si se subieron archivos
    if 'files' not in request.files:
        flash('No se seleccionaron archivos')
        return redirect(request.url)
    
    files = request.files.getlist('files')
    resp = {
        'dataframes': []
    }
    # Si no se seleccionaron archivos, mostrar mensaje
    if len(files) == 0 or files[0].filename == '':        
        flash('No se seleccionaron archivos')
    else:
        flash('Archivos subidos correctamente')
        for file in files:
            if file and allowed_file(file.filename):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)
                data = load_file(filepath)
                if data is None:
                    flash('Invalid file format')
                    return redirect(url_for('index'))
                # Vista previa de los primeros 5 registros
                preview = data.head().to_html(classes='data table table-striped', header="true", index=False)

                resp['dataframes'].append({
                    'filepath': filepath,
                    'preview': preview,
                    'columns': data.columns
                });

        return render_template('preview.html', **resp)

@app.route('/edit', methods=['POST'])
def edit_file():
    
    files_path = request.form.getlist('filepath_UP')
    
    resp = {
        'dataframes': []
    }
    index_Col = 0
    for filepath in files_path:
        data = load_file(filepath)
        print(str(filepath))
        
        # Obtener las opciones de edición del usuario
        columns_to_delete = request.form.getlist('columns_to_delete')
        print('Columnas a eliminar:'+str(columns_to_delete))
        new_names = request.form.getlist('new_names')
        print('Nuevos nombres:'+str(new_names))
        new_types = request.form.getlist('new_types')
        print('Nuevos tipos:'+str(new_types))
        nulos = request.form.get('eliminar_nulos')

        # Renombrar las columnas
        for idx, new_name in enumerate(new_names):
            if new_name and idx < len(data.columns):
                if data.columns.values[idx] in columns_to_delete:
                    indexNum = columns_to_delete.index(data.columns.values[idx])
                    columns_to_delete[indexNum] = new_name
                data.columns.values[idx] = new_name 
        
        # Eliminar columnas seleccionadas
        if columns_to_delete:
            data = data.drop(columns=columns_to_delete)
            
        # Cambiar tipos de datos
        for idx, new_type in enumerate(new_types):
            if new_type and idx < len(data.columns):
                try:
                    if new_type == 'int':
                        data[data.columns[idx]] = pd.to_numeric(data[data.columns[idx]], errors='coerce').fillna(0).astype(int)
                    elif new_type == 'float':
                        data[data.columns[idx]] = pd.to_numeric(data[data.columns[idx]], errors='coerce').astype(float)
                    elif new_type == 'str':
                        data[data.columns[idx]] = data[data.columns[idx]].astype(str)
                except Exception as e:
                    flash(f"Error al convertir columna {data.columns[idx]} a {new_type}: {str(e)}")
        
        
        # Eliminar duplicados y valores nulos
        if nulos:
            data = data.drop_duplicates().dropna()
        # Vista previa de los datos modificados
        preview = data.head().to_html(classes='data table table-striped', header="true", index=False)
        resp['dataframes'].append({
            'filepath': filepath,
            'preview': preview,
            'columns': data.columns
        });
        data.to_csv(filepath, index=False)
        index_Col = index_Col+1

    return render_template('preview.html', **resp)

@app.route('/combine', methods=['POST'])
def combine_files():
    filepaths = request.form.getlist('filepaths')
    dataframes = [load_file(filepath) for filepath in filepaths]

    # Verificar que los nombres de columnas y tipos de datos coincidan
    first_df_columns = list(dataframes[0].columns)
    first_df_dtypes = list(dataframes[0].dtypes)

    for df in dataframes[1:]:
        if list(df.columns) != first_df_columns or list(df.dtypes) != first_df_dtypes:
            flash('Las columnas o tipos de datos no coinciden en todos los archivos.')
            return redirect(url_for('index'))

    # Unir los DataFrames
    combined_df = pd.concat(dataframes)

    # Vista previa del DataFrame combinado
    preview = combined_df.head().to_html(classes='data', header="true", index=False)
    return render_template('preview.html', preview=preview)

if __name__ == '__main__':
    app.run(debug=True)
