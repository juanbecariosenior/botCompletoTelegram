from telegram import Update
from telegram.ext import ApplicationBuilder,CommandHandler,ContextTypes,filters,MessageHandler
import pyodbc
import asyncio
from decimal import Decimal

server = 'server'
bd = 'database'
usuario = 'usuario'
contrasena =  'contra'

async def inicio_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Bienvenido al Bot de consultas Kirest!\n\n Estos son los comandos disponibles:\n\n1. **Consultar comandas**\n\n\tUsa el comando `/comandas` para comenzar el flujo de consulta de comandas.\n\n2. **Consultar platillos por descripcion**\n\n\tUsa el comando `/platillosdesc` para comenzar el flujo de consulta de platillos por descripcion.\n\n3. **Consultar platillos por codigo**\n\n\tUsa el comando `/platillosplu` para comenzar el flujo de consulta de platillos por codigo.")

# Diccionario para almacenar los estados de los usuarios
usuarios = {}

async def consultar_comandas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicio del flujo para el comando /comandas."""
    user_id = update.effective_user.id
    usuarios[user_id] = {}  # Inicializa el espacio para este usuario
    texto = """
    **¡Bienvenido al Bot Consulta de Comandas!**

    Para realizar la consulta con éxito, sigue estos pasos:\n
    1. Ingresa un folio con el comando `/folio <número>`.\n 
       Ejemplo: `/folio 123`\n
    2. Ingresa una estación con el comando `/estacion <número>`. \n
       Ejemplo: `/estacion 34`\n
    3. Ingresa una sucursal con el comando `/sucursal <número>`.  \n
       Ejemplo: `/sucursal 1`\n

    **¡Empieza ingresando un folio ahora! :)**
    """
    await update.message.reply_text(texto, parse_mode="Markdown")

async def ingresar_folio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para ingresar un folio."""
    user_id = update.effective_user.id
    if user_id not in usuarios:
        await update.message.reply_text("Por favor, usa el comando /comandas para iniciar el proceso.")
        return
    
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Por favor, ingresa un folio válido. Ejemplo: /folio 123")
        return

    folio = args[0]
    usuarios[user_id]['folio'] = folio
    await update.message.reply_text(f"Folio '{folio}' guardado. Ahora ingresa la estación usando /estacion <número>.")

async def ingresar_estacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para ingresar una estación."""
    user_id = update.effective_user.id
    if user_id not in usuarios or 'folio' not in usuarios[user_id]:
        await update.message.reply_text("Por favor, usa el comando /comandas para iniciar el proceso.")
        return

    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Por favor, ingresa un número de estación válido. Ejemplo: /estacion 1")
        return

    estacion = args[0]
    usuarios[user_id]['estacion'] = estacion
    await update.message.reply_text(f"Estación '{estacion}' guardada. Ahora ingresa la sucursal usando /sucursal <número>.")

async def ingresar_sucursal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para ingresar una sucursal."""
    user_id = update.effective_user.id
    if user_id not in usuarios or 'folio' not in usuarios[user_id] or 'estacion' not in usuarios[user_id]:
        await update.message.reply_text("Por favor, usa el comando /comandas para iniciar el proceso.")
        return

    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Por favor, ingresa un número de sucursal válido. Ejemplo: /sucursal 34")
        return

    sucursal = args[0]
    usuarios[user_id]['sucursal'] = sucursal
    await update.message.reply_text(f"Sucursal '{sucursal}' guardada. Realizando consulta a la base de datos...")

    # Realizar la consulta
    datos = usuarios.get(user_id, {})
    resultado = obtener_datos(datos['folio'], datos['estacion'], datos['sucursal'])
    
    # Si se obtuvieron datos, formateamos y enviamos el mensaje
    if isinstance(resultado, list):
        mensaje_formateado = formatear_resultados(resultado)
        await update.message.reply_text(mensaje_formateado)
    else:
        # Si no se encontraron datos o hubo un error, enviamos el mensaje tal cual
        await update.message.reply_text(resultado)

    # Limpiar datos del usuario
    del usuarios[user_id]

def obtener_datos(folio, estacion, sucursal):
    """Consulta la base de datos con folio, estación y sucursal."""
    try:
        conexion = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL server}};SERVER={server};DATABASE={bd};UID={usuario};PWD={contrasena}'
        )
        cursor = conexion.cursor()
        # Llamar al procedimiento almacenado
        sp_nombre = "ObtenerDatosRemisiones"  # Reemplaza con el nombre real del procedimiento almacenado
        cursor.execute(f"EXEC {sp_nombre} ?, ?, ?", (folio, estacion, sucursal))
        datos = cursor.fetchall()
        cursor.close()
        conexion.close()
        return datos if datos else "No se encontraron datos."
    except Exception as e:
        return f"Error al consultar la base de datos: {e}"

def obtener_platillosdesc(precio_minimo):
    """Realiza la consulta SQL con un parámetro y devuelve los resultados."""
    try:
        conexion = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL server}};SERVER={server};DATABASE={bd};UID={usuario};PWD={contrasena}'
        )
        cursor = conexion.cursor()
        consulta = "Select Cod,Descripcion,Precio from RE_Platillos where Descripcion LIKE '%'+?+'%'"
        cursor.execute(consulta, (precio_minimo,))
        platillos = cursor.fetchall()
        cursor.close()
        conexion.close()
        return platillos
    except Exception as e:
        print(f"Error al consultar la base de datos: {e}")
        return None

def obtener_platillosplu(precio_minimo):
    """Realiza la consulta SQL con un parámetro y devuelve los resultados."""
    try:
        conexion = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL server}};SERVER={server};DATABASE={bd};UID={usuario};PWD={contrasena}'
        )
        cursor = conexion.cursor()
        consulta = "Select Cod,Descripcion,Precio from RE_Platillos where Cod = ?"
        cursor.execute(consulta, (precio_minimo,))
        platillos = cursor.fetchall()
        cursor.close()
        conexion.close()
        return platillos
    except Exception as e:
        print(f"Error al consultar la base de datos: {e}")
        return None
    
# Función para formatear los resultados
def formatear_resultados(resultados):
    mensaje = "Resultados de la consulta:\n\n"
    folio_anterior = None  # Variable para almacenar el último folio procesado
    
    for fila in resultados:
        folio, cod, descripcion, cant, pu, detalle, estacion, nombre, total, sucursal = fila
        
        # Si el folio cambia, cerramos el bloque anterior (si existe)
        if folio != folio_anterior:
            if folio_anterior is not None:
                # Imprimimos los detalles del folio anterior
                mensaje += f"Detalle: {detalle_anterior}\n"
                mensaje += f"Estación: {estacion_anterior}\n"
                mensaje += f"Mesero: {nombre_anterior}\n"
                mensaje += f"Total: ${total_anterior:,.2f}\n"
                mensaje += f"Sucursal: {sucursal_anterior}\n"
                mensaje += "-"*40 + "\n"
            
            # Imprimimos el nuevo folio
            mensaje += f"Folio: {folio}\n"
            mensaje += "-"*40 + "\n"
            folio_anterior = folio
            
            # Guardamos los detalles actuales para imprimir después
            detalle_anterior = detalle
            estacion_anterior = estacion
            nombre_anterior = nombre
            total_anterior = total
            sucursal_anterior = sucursal
        
        # Imprimimos los productos (estos van siempre)
        mensaje += f"Codigo: {cod}\n"
        mensaje += f"Descripción: {descripcion}\n"
        mensaje += f"Cantidad: {cant:.2f}\n"
        mensaje += f"Precio Unitario: ${pu:,.2f}\n"
        mensaje += "-"*40 + "\n"
    
    # Imprimimos los detalles del último folio al finalizar
    if folio_anterior is not None:
        mensaje += f"Detalle: {detalle_anterior}\n"
        mensaje += f"Estación: {estacion_anterior}\n"
        mensaje += f"Mesero: {nombre_anterior}\n"
        mensaje += f"Total: ${total_anterior:,.2f}\n"
        mensaje += f"Sucursal: {sucursal_anterior}\n"
        mensaje += "-"*40 + "\n"
    
    return mensaje




# Manejador genérico para mensajes no reconocidos
async def texto_invalido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "No reconozco este mensaje. Por favor, usa un comando válido como /comandas para iniciar."
    )

def dividir_mensaje(mensaje, max_longitud=4096):
    """Divide un mensaje en fragmentos más pequeños para cumplir con el límite de Telegram."""
    return [mensaje[i:i+max_longitud] for i in range(0, len(mensaje), max_longitud)]

async def mostrar_platillosdesc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador del comando /platillos con un parámetro dinámico."""
    try:
        # Obtener el parámetro del mensaje del usuario
        args = context.args
        if not args or not args[0].isalpha():
            await update.message.reply_text("Por favor, especifica una breve descripción del platillo. Ejemplo: /platillosdesc hamburguesa")
            return
        
        desc_platillo = args[0]
        await update.message.reply_text(f"Consultando platillos con una descripción similar a '{desc_platillo}', por favor espera...")
        
        # Ejecutar la consulta SQL en un hilo separado
        loop = asyncio.get_event_loop()
        platillos = await loop.run_in_executor(None, obtener_platillosdesc, desc_platillo)
        
        # Formatear los resultados
        if platillos:
            respuesta = "Platillos disponibles:\n"
            respuesta += "\n".join([f"{cod}: {desc} - ${precio:.2f}" for cod, desc, precio in platillos])
        else:
            respuesta = f"No se encontraron platillos con una descripción similar a '{desc_platillo}'."
        
        # Dividir el mensaje si es muy largo
        fragmentos = dividir_mensaje(respuesta)
        for fragmento in fragmentos:
            await update.message.reply_text(fragmento)
    except Exception as e:
        await update.message.reply_text(f"Ocurrió un error: {e}")

async def mostrar_platillosplu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador del comando /platillos con un parámetro dinámico."""
    try:
        # Obtener el parámetro del mensaje del usuario
        args = context.args
        if not args or not args[0].isdigit():
            await update.message.reply_text("Por favor, especifica un codigo del platillo. Ejemplo: /platillosplu 101")
            return
        
        codigo_platillo = args[0]
        await update.message.reply_text(f"Consultando platillos con un codigo similar a '{codigo_platillo}', por favor espera...")
        
        # Ejecutar la consulta SQL en un hilo separado
        loop = asyncio.get_event_loop()
        platillos = await loop.run_in_executor(None, obtener_platillosplu, codigo_platillo)
        
        # Formatear los resultados
        if platillos:
            respuesta = "Platillos disponibles:\n"
            respuesta += "\n".join([f"{cod}: {desc} - ${precio:.2f}" for cod, desc, precio in platillos])
        else:
            respuesta = f"No se encontraron platillos con un codigo similar a '{codigo_platillo}'."
        
        # Dividir el mensaje si es muy largo
        fragmentos = dividir_mensaje(respuesta)
        for fragmento in fragmentos:
            await update.message.reply_text(fragmento)
    except Exception as e:
        await update.message.reply_text(f"Ocurrió un error: {e}")




application = ApplicationBuilder().token("token").build()
application.add_handler(CommandHandler("start", inicio_bot))
application.add_handler(CommandHandler("comandas", consultar_comandas))
application.add_handler(CommandHandler("platillosdesc", mostrar_platillosdesc))
application.add_handler(CommandHandler("platillosplu", mostrar_platillosplu))
application.add_handler(CommandHandler("folio", ingresar_folio))
application.add_handler(CommandHandler("estacion", ingresar_estacion))
application.add_handler(CommandHandler("sucursal", ingresar_sucursal))

# Manejador genérico
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, texto_invalido))
application.run_polling(allowed_updates=Update.ALL_TYPES)
