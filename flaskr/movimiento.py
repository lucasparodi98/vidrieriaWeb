import re
import json
import os
import folium
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.utils import secure_filename
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.db import get_db
from datetime import datetime
from flaskr.funciones import *

bp = Blueprint('movimiento', __name__)

#Obtiene movimiento en la base de datos segun el ID
def get_movimiento(id, check_user=True):
    movimiento = get_db().execute(
        """
        SELECT m.id, fecha_creacion, tipo, destino, comentario, monto
        FROM movimiento m JOIN user u ON m.user_id = u.id
        WHERE i.id = ?',
        """
        (id,)
    ).fetchone()

    if movimiento is None:
        abort(404, f"Post id {id} doesn't exist.")

    #Revisa que el usuario que edita solo sea el mismo que lo creo
    #if check_user and inf_red['user_id'] != g.user['id']:
    #    abort(403)

    return movimiento

@bp.route('/movimiento')
@login_required
def indexMovimiento():
    db = get_db()
    movimientos = db.execute(
        """
        SELECT m.id, fecha_creacion, tipo, destino, comentario, monto
        FROM movimiento m JOIN user u ON m.user_id = u.id
        ORDER BY fecha_creacion DESC
        """
    ).fetchall()
    n = len(movimientos)

    style_cell_tipo = []
    for movimiento in movimientos:
        if movimiento['tipo'] == 'Entrada':
            style_cell_tipo.append('color: #006100;background-color: #c6efce;')
        elif movimiento['tipo'] == 'Salida':
            style_cell_tipo.append('color: #9c0006;background-color: #ffc7ce;')

    return render_template('movimiento/index.html', movimientos=movimientos, n=n, style_cell_tipo=style_cell_tipo)

@bp.route('/movimiento/create', methods=('GET', 'POST'))
@login_required
def createMovimiento():

    if request.method == 'POST':
        tipo = request.form['tipo']
        destino = request.form['destino']
        comentario = request.form['comentario']
        monto = request.form['monto']

        error = None


        if error is not None:
            flash(error)
        #Registrar nueva entrada en la base de datos
        else:

            db = get_db()
            db.execute(
                """
                INSERT INTO movimiento (fecha_creacion, user_id, tipo, destino, comentario, monto)
                 VALUES ((datetime('now','localtime')), ?, ?, ?, ?, ?)
                """,
                (g.user['id'], tipo, destino, comentario, monto)
            )
            db.commit()

            return redirect(url_for('movimiento.indexMovimiento'))

    return render_template('movimiento/create.html')

@bp.route('/inf_red/<string:id>/update', methods=('GET', 'POST'))
@login_required
def updateInfRed(id):
    inf_red = get_inf(id)

    db_departamentos = get_db().execute(
        'SELECT departamento'
        ' FROM departamentos'
        ' ORDER BY departamento'
    ).fetchall()

    if request.method == 'POST':
        documento = request.form['documento']
        link_archivos = request.form['link_archivos']
        fecha_documento = request.form['fecha_documento']
        titulo_correo = request.form['titulo_correo']
        fecha_correo = request.form['fecha_correo']
        nombre_entidad = request.form['nombre_entidad']
        entidad = request.form['entidad']
        proyecto = request.form['proyecto']
        departamento = request.form['departamento']
        provincia = request.form['provincia']
        distrito = request.form['distrito']
        contacto = request.form['contacto']
        correo_contacto = request.form['correo_contacto']
        telefono_contacto = request.form['telefono_contacto']
        resumen_planta = request.form['resumen_planta']
        fecha_respuesta = request.form['fecha_respuesta']
        tma = request.form['tma']
        estado_inf_red = request.form['estado_inf_red']
        estado_proyecto = request.form['estado_proyecto']
        peso_kml = request.form['peso_kml']
        formulario_completado = request.form['formulario_completado']
        inicio_obras = request.form['inicio_obras']
        complejidad = request.form['complejidad']
        archivoKML = request.files["archivoKML"]

        observacion = request.form["observacion"]
        error = None

        if not documento:
            error = 'Documento is required.'
        if archivoKML.filename != '' and not(allowed_file(archivoKML.filename)):
            error = 'Formato del archivo incorrecto'

        if error is not None:
            flash(error)
        else:
            if archivoKML.filename != '':
                filename = secure_filename(archivoKML.filename)
                archivoKML.save(filename)
                json_coords = get_coordinates(filename)
                os.remove(filename)
            else:
                json_coords = inf_red['json_coords']

            #Validar Cambios
            tipo_comentario = 'Comentario'
            texto_comentario = ''
            if inf_red['estado_inf_red'] != estado_inf_red:
                tipo_comentario = 'Actualización'
                texto_comentario = texto_comentario + 'Cambio estado Inf. de Red de <b>' + str(inf_red['estado_inf_red']) + '</b> a <b>' + str(estado_inf_red) + '</b>'
            if inf_red['estado_proyecto'] != estado_proyecto:
                tipo_comentario = 'Actualización'
                if texto_comentario == '':
                    texto_comentario = texto_comentario + 'Cambio Estado del Proyecto de <b>' + str(inf_red['estado_proyecto']) + '</b> a <b>' + str(estado_proyecto) + '</b>'
                else:
                    texto_comentario = texto_comentario + '<br>Cambio Estado del Proyecto de <b>' + str(inf_red['estado_proyecto']) + '</b> a <b>' + str(estado_proyecto) + '</b>'
            if inf_red['inicio_obras'] != inicio_obras:
                tipo_comentario = 'Actualización'
                if texto_comentario == '':
                    texto_comentario = texto_comentario + 'Cambio Inico de Obras de <b>' + str(inf_red['inicio_obras']) + '</b> a <b>' + str(inicio_obras) + '</b>'
                else:
                    texto_comentario = texto_comentario + '<br>Cambio Inico de Obras de <b>' + str(inf_red['inicio_obras']) + '</b> a <b>' + str(inicio_obras) + '</b>'
            if inf_red['nombre_entidad'] != nombre_entidad:
                tipo_comentario = 'Actualización'
                if texto_comentario == '':
                    texto_comentario = texto_comentario + 'Cambio Entidad de <b>' + str(inf_red['nombre_entidad']) + '</b> a <b>' + str(nombre_entidad) + '</b>'
                else:
                    texto_comentario = texto_comentario + '<br>Cambio Entidad de <b>' + str(inf_red['nombre_entidad']) + '</b> a <b>' + str(nombre_entidad) + '</b>'

            if observacion:
                if texto_comentario == '':
                    texto_comentario = texto_comentario + str(observacion)
                else:
                    texto_comentario = texto_comentario + '<br><b>Observación</b><br>' + str(observacion)


            db = get_db()
            db.execute(
                'UPDATE inf_red SET documento = ?, link_archivos = ?, fecha_documento = ?, titulo_correo = ?, fecha_correo = ?, nombre_entidad = ?, entidad = ?, proyecto = ?, departamento = ?, provincia = ?, distrito = ?, contacto = ?, correo_contacto = ?, telefono_contacto = ?, resumen_planta = ?, fecha_respuesta = ?, tma = ?, estado_inf_red = ?, estado_proyecto = ?, peso_kml = ?, formulario_completado = ?, inicio_obras = ?, complejidad = ?, json_coords = ?'
                ' WHERE id = ?',
                (documento, link_archivos, fecha_documento, titulo_correo, fecha_correo, nombre_entidad, entidad, proyecto, departamento, provincia, distrito, contacto, correo_contacto, telefono_contacto, resumen_planta, fecha_respuesta, tma, estado_inf_red, estado_proyecto, peso_kml, formulario_completado, inicio_obras, complejidad, json_coords, id)
            )
            db.commit()

            #Agregar Historial
            if texto_comentario != '':
                db.execute(
                    """
                    INSERT INTO historial (user_id, fecha, cod_unico, tipo, observacion)
                    VALUES (?, (datetime('now','localtime')), ?, ?, ?)
                    """,
                    (g.user['id'], id, tipo_comentario, texto_comentario)
                )
                db.commit()

            return redirect(url_for('inf_red.viewAll', id = id))

    return render_template('inf_red/update.html', inf_red=inf_red, departamentos = db_departamentos)

@bp.route('/inf_red/<string:id>/delete', methods=('POST',))
@login_required
def deleteInfRed(id):
    get_inf(id)
    db = get_db()
    db.execute('DELETE FROM inf_red WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('inf_red.indexInfRed'))

@bp.get('/provincia')
def provincia():
    departamento = request.args.get('departamento')
    db_provincias = get_db().execute(
        'SELECT departamento, provincia'
        ' FROM provincias'
        ' WHERE departamento = ?',
        (departamento,)
    ).fetchall()
    return render_template('utilidad/provincia_options.html', provincias = db_provincias)

@bp.get('/distrito')
def distrito():
    provincia = request.args.get('provincia')
    db_distritos = get_db().execute(
        'SELECT departamento, provincia, distrito'
        ' FROM distritos'
        ' WHERE provincia = ?',
        (provincia,)
    ).fetchall()
    return render_template('utilidad/distrito_options.html', distritos = db_distritos)

#Función que muestra todo el detalle de un Código Único
@bp.route('/obra_publica/<string:id>')
@login_required
def viewAll(id):
    inf_red = get_inf(id)
    presupuestos = get_presupuesto(id)
    #Generar lista de Estados Generales si hay 1 o más presupuestos
    if len(presupuestos) > 0:
        estado_general = []
        for presupuesto in presupuestos:
            estado_general.append(get_db().execute(
                """
                    SELECT grupo_estado
                    FROM estadosOP
                    WHERE estado = ?
                """,
                (presupuesto['estado'],)
            ).fetchone()[0])
    else:
        estado_general = get_estado_grupo_infred(inf_red["estado_inf_red"])
    
    estado_general_html = []
    for i in range(len(estado_general)):
        if len(presupuestos) > 0:
            estado_general_html.append("<i style='color:" + get_color_estado(estado_general[i]) +";'>" + presupuestos[i]['estado'] + "</i>")
        else:
            estado_general_html.append("<i style='color:" + get_color_estado(estado_general[i]) +";'>" + estado_general[i] + "</i>")

    color = get_color_estado(estado_general)
    list_class = get_estado_grupo_class(estado_general)

    list_historial = []
    #Historial Inf de Red
    historial = get_db().execute(
        """
        SELECT h.fecha, h.cod_unico, 'Inf. Red' AS ip_madre, u.username, h.observacion
        FROM historial h 
        LEFT JOIN user u ON h.user_id = u.id
        LEFT JOIN presupuesto p ON h.cod_unico = p.cod_unico
        WHERE h.cod_unico = ? AND h.presupuesto_id IS NULL
		GROUP BY h.fecha
        ORDER BY h.fecha DESC
        """,
        (id,)
    ).fetchall()
    list_historial.append([historial, '<b>Historial Inf. Red</b>', 'inf_redA'])
    #Historial de cada presupuesto
    for presupuesto in presupuestos:
        historial = get_db().execute(
            """
            SELECT h.fecha, h.cod_unico, p.ip_madre, u.username, h.observacion
            FROM historial h 
            LEFT JOIN user u ON h.user_id = u.id
            LEFT JOIN presupuesto p ON h.cod_unico = p.cod_unico
            WHERE h.presupuesto_id = ?
            GROUP BY h.fecha
            ORDER BY h.fecha DESC
            """,
            (presupuesto['id'],)
        ).fetchall()
        list_historial.append([historial, '<b>IP Madre </b>' + str(presupuesto['ip_madre']) + '<br><b>Bautizo </b>' + str(presupuesto['bautizo']),
                               str(presupuesto['id'])])

    init_coord = []
    if inf_red["json_coords"] != '' and inf_red["json_coords"] != None:
        coordinates = json.loads(inf_red["json_coords"])
        #Obtener coordenadas para localizacion inicial
        for coor_type in coordinates:
            if coor_type[0] == 'Points':
                for points in coor_type[1]:
                    for point in points:
                        init_coord = point
                        break
                    if len(init_coord) > 0:
                        break
            elif coor_type[0] == 'LineStrings':
                for line in coor_type[1]:
                    for point in line:
                        init_coord = point
                        break
                    if len(init_coord) > 0:
                        break
            elif coor_type[0] == 'Polygons':
                for pol in coor_type[1]:
                    for point in pol:
                        init_coord = point
                        break
                    if len(init_coord) > 0:
                        break
            if len(init_coord) > 0:
                break

    if len(init_coord) == 0:
        init_coord = [-9, -75]

    fig_map = folium.Map(location=init_coord, zoom_start=15)

    if inf_red["json_coords"] != '' and inf_red["json_coords"] != None:
        draw_figures(fig_map, inf_red, estado_general)

    plugins.Geocoder().add_to(fig_map)
    plugins.Fullscreen(
        position                = "topright",
        title                   = "Open full-screen map",
        title_cancel            = "Close full-screen map",
        force_separate_button   = True,
    ).add_to(fig_map)

    iframe = fig_map.get_root()._repr_html_()

    return render_template('/view.html', inf_red=inf_red, iframe=iframe, list_historial=list_historial,
                           list_class=list_class, presupuestos=presupuestos, num_estados=len(estado_general), estado_general=estado_general_html)

@bp.route('/comentario/<string:cu>/<string:comentario>')
def add_comentario(cu, comentario):
    db = get_db()
    db.execute(
            """
            INSERT INTO historial (user_id, fecha, cod_unico, tipo, observacion)
             VALUES (?, (datetime('now','localtime')), ?, ?, ?)
            """,
            (g.user['id'], cu, "Comentario", comentario)
        )
    db.commit()
    return ('', 204)