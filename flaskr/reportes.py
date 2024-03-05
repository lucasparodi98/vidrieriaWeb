import re
import json
import os
import folium

import pandas as pd

from flask import (
    Blueprint, flash, g, redirect, render_template, render_template_string, request, url_for, send_file
)
from werkzeug.utils import secure_filename
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.db import get_db
from datetime import datetime
from pykml import parser
from folium import plugins
from flaskr.funciones import *

from datetime import date
import locale


bp = Blueprint('reportes', __name__)

def draw_departamentos(fig, data, num_proyectos):
    #Elaborar un Mapa
    coordinates = json.loads(data["json_coords"])
    tooltip = str(data["departamento"])

    html = "<p><b>" + data["departamento"] + "</b></p><p>N° Proyectos: " + str(num_proyectos) + "</p>"
    iframe = folium.IFrame(html)

    for coor_type in coordinates:
        
        if coor_type[0] == 'Points':
            for point in coor_type[1]:
                popUp = folium.Popup(iframe, min_width=150, max_width=150)
                print(str(data["departamento"]) + "Punto")
                folium.Marker(
                point[0], popup=popUp, tooltip=tooltip
                ).add_to(fig)
        elif coor_type[0] == 'LineStrings':
            for line in coor_type[1]:
                popUp = folium.Popup(iframe, min_width=150, max_width=150)
                print(str(data["departamento"]) + "linea")
                folium.PolyLine(
                line, color="blue", weight=4, opacity=0.5, popup=popUp, tooltip=tooltip
                ).add_to(fig)
        elif coor_type[0] == 'Polygons':
            for pol in coor_type[1]:
                popUp = folium.Popup(iframe, min_width=150, max_width=150)
                print(str(data["departamento"]) + "poligono")
                folium.PolyLine(
                pol, color="#000000", fill_color=data["color"], weight=1 , popup=popUp, tooltip=tooltip
                ).add_to(fig)
    return fig

def draw_figures(fig, data, estado):
    coordinates = json.loads(data["json_coords"])
    tooltip = str(data["id"])
    color = get_color_estado(estado)
    html = "<b style=''>" + data["proyecto"] + "</b><br><i>" + data["entidad"] + "</i><br>" + estado + "<br><a href='../obra_publica/" + str(data["id"]) + "' target='_blank'><button class='btn btn-info'>Ver Detalle</button></a>"
    html = """
        <style type="text/css">
            
        </style>

        <b style='font-size:small;'>{proyecto}</b>
        <br>
        <i>{entidad}</i>
        <br>
        {estado}
        <br>
        <a href='{root}/obra_publica/{id}' target='_blank'><button>Ver Detalle</button></a>
    """.format(proyecto=data["proyecto"], entidad=data["entidad"], estado=estado, id=data["id"], root=request.url_root )

    
    iframe = folium.IFrame(html)
    width = 300

    for coor_type in coordinates:
        if coor_type[0] == 'Points':
            for point in coor_type[1]:
                popUp = folium.Popup(iframe, min_width=width, max_width=width)
                folium.CircleMarker(
                point[0], color=color, opacity=0.8, popup=popUp, tooltip=tooltip,
                ).add_to(fig)
        elif coor_type[0] == 'LineStrings':
            for line in coor_type[1]:
                popUp = folium.Popup(iframe, min_width=width, max_width=width)
                folium.PolyLine(
                line, color=color, weight=4, opacity=0.8, popup=popUp, tooltip=tooltip,
                ).add_to(fig)
        elif coor_type[0] == 'Polygons':
            for pol in coor_type[1]:
                popUp = folium.Popup(iframe, min_width=width, max_width=width)
                folium.PolyLine(
                pol, color=color, fill_color=color, opacity=0.8, popup=popUp, tooltip=tooltip,
                ).add_to(fig)
    return fig

def create_fig(all_data):
    fig_map = folium.Map(location=[-9, -75], zoom_start=6)
    for data in all_data:
        if data["json_coords"] != '' and data["json_coords"] != None:
            if data['grupo'] in ['', None]:
                estado = get_estado_grupo_infred(data["estado_inf_red"])[0]
            else:
                estado = data['grupo']

            fig_map = draw_figures(fig_map, data, estado)
    plugins.Geocoder().add_to(fig_map)
    plugins.Fullscreen(
        position                = "topright",
        title                   = "Open full-screen map",
        title_cancel            = "Close full-screen map",
        force_separate_button   = True,
    ).add_to(fig_map)
    return(fig_map.get_root()._repr_html_())

@bp.route('/reporte/departamentos')
@login_required
def viewDepartamentos():
    db = get_db()
    departamentos = db.execute(
        'SELECT id, departamento, color, json_coords'
        ' FROM departamentos'
    ).fetchall()

    fig_map = folium.Map(location=[-9, -75], zoom_start=6)

    for data in departamentos:
        num_proyectos = db.execute(
            'SELECT COUNT(*)'
            ' FROM inf_red'
            ' WHERE departamento = ?',
            (data['departamento'],)
        ).fetchone()[0]
        fig_map = draw_departamentos(fig_map, data, num_proyectos)

    plugins.Geocoder().add_to(fig_map)
    plugins.Fullscreen(
        position                = "topright",
        title                   = "Open full-screen map",
        title_cancel            = "Close full-screen map",
        force_separate_button   = True,
    ).add_to(fig_map)

    iframe = fig_map.get_root()._repr_html_()

    return render_template('/reportes/departamentos.html', iframe=iframe)

@bp.route('/reporte/obras_publicas', methods=('GET', 'POST'))
@login_required
def viewAll():
    years = [[2022, 1], [2023, 1], [2024, 1]]
    departamentos = get_db().execute(
        'SELECT departamento, 1 as checked'
        ' FROM departamentos'
        ' ORDER BY departamento ASC'
    ).fetchall()
    estadosOP = get_db().execute(
        'SELECT DISTINCT grupo_estado_general, 1 as checked'
        ' FROM estadosOP'
    ).fetchall()

    #Convertir a lista
    temp = []
    for departamento in departamentos:
        temp.append([departamento['departamento'], departamento['checked']])
    departamentos = temp

    temp = []
    temp.append(['En proceso de Información de Red', 1])
    temp.append(['Información de Red enviado a Entidad', 1])
    for estado in estadosOP:
        temp.append([estado['grupo_estado_general'], estado['checked']])
    estadosOP = temp

    all_data = get_db().execute(
        """
        SELECT i.id, i.proyecto, i.estado_inf_red, i.entidad, p.estado, e.grupo_estado_general AS grupo, i.json_coords
        FROM inf_red i
        LEFT JOIN presupuesto p ON i.id = p.cod_unico
        LEFT JOIN estadosOP e ON p.estado = e.estado
        """
    ).fetchall()

    if request.method == 'POST':
        year_post = request.form.getlist('year_post')
        departamento_post = request.form.getlist('departamento_post')
        estado_post = request.form.getlist('estado_post')

        all_data = get_db().execute(
            """
            SELECT i.id, i.proyecto, i.estado_inf_red, i.entidad, p.estado, i.json_coords,
            CASE WHEN e.grupo_estado_general IS NULL
            THEN 
                CASE WHEN i.estado_inf_red IN ('PENDIENTE','EN PROCESO')
                THEN 'En proceso de Información de Red'
                ELSE 
                    CASE WHEN i.estado_inf_red = 'ATENDIDO'
                    THEN 'Información de Red enviado a Entidad'
                    ELSE 'Desestimado'
                    END
                END
            ELSE e.grupo_estado_general
            END AS grupo
            FROM inf_red i
            LEFT JOIN presupuesto p ON i.id = p.cod_unico
            LEFT JOIN estadosOP e ON p.estado = e.estado
            WHERE SUBSTR(i.id, 1, 4) IN (""" + ','.join([str("'" + str(x) + "'") for x in tuple(year_post)]) + """)
            AND i.departamento IN (""" + ','.join([str("'" + str(x) + "'") for x in tuple(departamento_post)]) + """)
            AND grupo IN (""" + ','.join([str("'" + str(x) + "'") for x in tuple(estado_post)]) + """)
            """
        ).fetchall()
        iframe = create_fig(all_data)
        #Deseleccionar del filtro los que no estén seleccionados
        for year in years:
            if not str(year[0]) in year_post:
                year[1] = 0

        for departamento in departamentos:
            if not departamento[0] in departamento_post:
                departamento[1] = 0

        for estado in estadosOP:
            if not estado[0] in estado_post:
                estado[1] = 0

        return render_template('/reportes/mapa_consolidado.html', iframe=iframe, years=years, departamentos=departamentos, estadosOP=estadosOP)


    iframe = create_fig(all_data)
    return render_template('/reportes/mapa_consolidado.html', iframe=iframe, years=years, departamentos=departamentos, estadosOP=estadosOP)

@bp.route('/reporte/objetivos')
@login_required
def objetivos():
    locale.setlocale(locale.LC_TIME, 'es_PE.UTF-8')    
    mes_actual = date.today().strftime('%B').capitalize()
    porcentaje_mes_actual = date.today().month/12*100
    trimestres = {'Enero': 'Primer Trimestre', 'Febrero': 'Primer Trimestre', 'Marzo': 'Primer Trimestre', 'Abril': 'Segundo Trimestre', 'Mayo':'Segundo Trimestre', 'Junio':'Segundo Trimestre', 'Julio':'Tercer Trimestre', 'Agosto':'Tercer Trimestre', 'Setiembre':'Tercer Trimestre', 'Octubre':'Cuarto Trimestre', 'Noviembre': 'Cuarto Trimestre', 'Diciembre':'Cuarto Trimestre'}
    trimestre_actual = trimestres[mes_actual]
    trim = ','.join(["'"+k+"'" for k, v in trimestres.items() if v == trimestre_actual])
    

    dias_cierre=str((date(2024, 12, 15)-date.today()).days)

    proyeccion_pago = get_db().execute(
    """SELECT  SUM(montoIGV),  mes_pago_oficial
        FROM presupuesto
        WHERE SUBSTR(mes_pago_oficial, -1) IN ('4') """).fetchall()
    proyeccion_pago = round(proyeccion_pago[0][0]/1000000,1)
    sobrecumplimiento = round(10-proyeccion_pago,1)


    inf_plan_pago = get_db().execute(
    """SELECT  p.montoIGV, p.ip_madre, p.mes_pago_oficial, p.semana_pago_oficial, p.bautizo, p.semana_pago_interno, p.mes_pago_planificado, i.entidad, p.estado, i.entidad, p.cod_unico
        FROM presupuesto p
        LEFT JOIN inf_red i ON p.cod_unico = i.id
        WHERE SUBSTR(mes_pago_oficial, -1) = '4'""").fetchall()
    meses_plan_pago = get_db().execute(
    """SELECT  mes_pago_oficial, count(*) AS cant, sum(montoIGV) as monto
        FROM presupuesto 
        WHERE SUBSTR(mes_pago_oficial, -1) = '4'
        GROUP BY mes_pago_oficial
        ORDER BY CASE mes_pago_oficial
            WHEN 'Febrero 2024' THEN 0
            WHEN 'Marzo 2024' THEN 1
            WHEN 'Abril 2024' THEN 2
            WHEN 'Mayo 2024' THEN 3
            WHEN 'Junio 2024' THEN 4
            WHEN 'Julio 2024' THEN 5
            WHEN 'Agosto 2024' THEN 6
            WHEN 'Setiembre 2024' THEN 7
            WHEN 'Octubre 2024' THEN 8
            WHEN 'Noviembre 2024' THEN 9
            WHEN 'Diciembre 2024' THEN 10
        END """).fetchall()
    suma_plan_pago = get_db().execute(
    """SELECT  sum(montoIGV)
        FROM presupuesto p
        WHERE SUBSTR(mes_pago_oficial, -1) = '4'""").fetchall()
    


    plan_ofi = get_db().execute(
        """ SELECT  mes_pago_oficial,sum(montoIGV) 
            FROM  presupuesto
            WHERE SUBSTR(mes_pago_oficial, -1) IN ('4')
            GROUP BY mes_pago_oficial   """ ).fetchall()
    #pago_meses[0][0]  devuelve valor de la primera fila de la columna mes_pago_oficial
    #pago_meses[0][1]  devuelve valor de la primera fila de la columna sum(montoIGV)
    #pago_meses[1][1]  devuelve valor de la segunda fila de la columna sum(montoIGV)  
    meses = {'Ene': 0, 'Feb': 0, 'Mar': 0, 'Abr': 0, 'May':0, 'Jun':0, 'Jul':0, 'Ago':0, 'Set':0, 'Oct':0, 'Nov': 0, 'Dic':0}
    for mes in plan_ofi:
        try:   
            if mes[1]>=1000000:
                meses[mes[0][0:3]] = round(mes[1]/1000000,1)
            else: 
                meses[mes[0][0:3]] = round(mes[1]/1000000,3) 
        except:
            pass
    pago_ofi_mens = list(meses.values())
    pago_ofi_trim = [meses['Ene']+meses['Feb']+meses['Mar'], meses['Abr']+meses['May']+meses['Jun'], meses['Jul']+meses['Ago']+meses['Set'], meses['Oct']+meses['Nov']+meses['Dic']]
    pago_ofi_trim = [round(i,1) if i>1 else round(i,3) for i in pago_ofi_trim]
    

    plan_int = get_db().execute(
        """SELECT  mes_pago_planificado,sum(montoIGV) 
            FROM  presupuesto p
            LEFT JOIN estadosOP e ON p.estado = e.estado
            WHERE e.grupo_gestion IN ('EN COORDINACIÓN') AND p.prioridad IN ('GESTION 2023', 'GESTION 2024', 'EBC')
            GROUP BY mes_pago_planificado   """ ).fetchall()
    meses = {'Ene': 0, 'Feb': 0, 'Mar': 0, 'Abr': 0, 'May':0, 'Jun':0, 'Jul':0, 'Ago':0, 'Set':0, 'Oct':0, 'Nov': 0, 'Dic':0, 'Sin':0, '':0}
    for mes in plan_int:
        try:   
            if mes[1]>=1000000:
                meses[mes[0][0:3]] = round(mes[1]/1000000,1)
            else: 
                meses[mes[0][0:3]] = round(mes[1]/1000000,3) 
        except:
            pass
    meses['Sin']=round(meses['Sin']+meses[''],1)
    meses.pop('', None)
    pago_int_mens = list(meses.values())
    pago_int_trim = [meses['Ene']+meses['Feb']+meses['Mar'], meses['Abr']+meses['May']+meses['Jun'], meses['Jul']+meses['Ago']+meses['Set'], meses['Oct']+meses['Nov']+meses['Dic'],meses['Sin'],0]
    pago_int_trim = [round(i,1) if i>1 else round(i,3) for i in pago_int_trim]


    ppto_emitido = get_db().execute(
        """SELECT  sum(montoIGV) 
            FROM  presupuesto p
            LEFT JOIN estadosOP e ON p.estado = e.estado
            WHERE e.grupo_gestion IN ('EN COORDINACIÓN') AND p.prioridad IN ('GESTION 2023', 'GESTION 2024', 'EBC')""" ).fetchall()
    ppto_emitido = str(round(ppto_emitido[0][0]/1000000,1)) + ' MM'


    cronograma_mes_actual = get_db().execute(
        """ SELECT  semana_pago_oficial, bautizo_corto, montoIGV
            FROM  presupuesto
            WHERE SUBSTR(mes_pago_oficial, -1) = '4'  AND SUBSTR(mes_pago_oficial, 0, INSTR(mes_pago_oficial, ' ')) = '""" + mes_actual + """' """
             ).fetchall()   
    semanas = {i['semana_pago_oficial'] for i in cronograma_mes_actual}


    inf_pagado = get_db().execute(
        """SELECT  SUM(montoIGV),  estado
        FROM presupuesto
        WHERE SUBSTR(estado, -1) IN ('4') """ ).fetchall()
    try:
        if inf_pagado[0][0]>1000000 or inf_pagado[0][0]==0:
            facturado = round(inf_pagado[0][0]/1000000,1)
        else:
            facturado = round(inf_pagado[0][0]/1000,1)
    except:
        facturado = 0


    inf_revision = get_db().execute(
        """SELECT  SUM(montoIGV),  mes_pago_oficial
        FROM presupuesto
        WHERE SUBSTR(mes_pago_oficial, 0, INSTR(mes_pago_oficial, ' ')) IN  ( """ + trim + """ ) """).fetchall()
    try:
        if inf_revision[0][0]>1000000 or inf_pagado[0][0]==0:
            revision = round(inf_revision[0][0]/1000000,1)
        else:
            revision = round(inf_revision[0][0]/1000,1)
    except:
        revision = 0


    avance = get_db().execute(
        """ SELECT  mes_pago_oficial,sum(montoIGV) 
            FROM  presupuesto
            WHERE SUBSTR(mes_pago_oficial, 0, INSTR(mes_pago_oficial, ' ')) = ' """ + mes_actual + """ ' """).fetchall()



    return render_template('/reportes/objetivos.html',  meses_plan_pago=meses_plan_pago, dias_cierre=dias_cierre, suma_plan_pago=suma_plan_pago, inf_plan_pago=inf_plan_pago, facturado=facturado, revision=revision, proyeccion_pago=proyeccion_pago, sobrecumplimiento=sobrecumplimiento,  pago_ofi_mens=pago_ofi_mens, pago_ofi_trim=pago_ofi_trim, pago_int_mens=pago_int_mens, pago_int_trim=pago_int_trim, ppto_emitido=ppto_emitido, cronograma_mes_actual=cronograma_mes_actual, mes_actual=mes_actual, semanas=semanas, avance=avance, porcentaje_mes_actual=porcentaje_mes_actual)

@bp.route('/reporte/proyectos_gestionados_2024')
@login_required
def proyectos_gestionados_2024():
    vista_general = get_db().execute(
    """SELECT  e.id, e.grupo_gestion, p.estado, CAST (sum(p.montoIGV) AS INT) AS montoIGV, count(p.ip_madre) AS proy
        FROM presupuesto p
        LEFT JOIN estadosOP e ON p.estado = e.estado
        WHERE p.prioridad IN ('GESTION 2023', 'GESTION 2024', 'EBC')
        GROUP BY p.estado 
        ORDER BY e.id""").fetchall()
    vista_general_grupos = get_db().execute(
    """ SELECT grupo_gestion, sum(cant) AS proy, count(*) AS cant, sum(montoIGV) AS montoIGV
        FROM
        (SELECT  e.grupo_gestion AS grupo_gestion, count(p.estado) AS cant, CAST (sum(p.montoIGV) AS INT) AS montoIGV, p.estado
        FROM presupuesto p
        LEFT JOIN estadosOP e ON p.estado = e.estado
        WHERE p.prioridad IN ('GESTION 2023', 'GESTION 2024', 'EBC')
        GROUP BY p.estado)
        GROUP BY grupo_gestion
        ORDER BY 
        CASE grupo_gestion
            WHEN 'FACTURADO ' THEN 0
            WHEN 'EN COORDINACIÓN' THEN 1
            WHEN 'PREVIO AL PRESUPUESTO' THEN 2
            WHEN 'SIN RPTA ENTIDAD' THEN 3
            WHEN 'SIN RTPA DE LA ENTIDAD, EN COORDINACIÓN CON EQ. REGULACIÓN' THEN 4
            WHEN 'ANTEPROYECTO' THEN 5
            WHEN 'LA ENTIDAD NO ACEPTA EL PRESUPUESTO' THEN 6
        END""").fetchall()
    
    
    con_ip_sin_oc = get_db().execute(
    """SELECT  i.nombre_entidad, p.cod_unico, p.ip_madre, p.bautizo, p.estado_ipmadre_webPO, p.solicitudOC, CAST((julianday('now') - julianday(p.fecha_creacion_ipmadre)) AS INTEGER) AS dias_transc
        FROM presupuesto p
        LEFT JOIN inf_red i ON p.cod_unico = i.id
        WHERE p.prioridad IN ('GESTION 2023', 'GESTION 2024', 'EBC') AND p.estado = 'Diseño pendiente - IP MADRE sin orden de compra' """).fetchall()
    
    en_diseño = get_db().execute(
    """SELECT  i.nombre_entidad, p.cod_unico, p.ip_madre, p.bautizo, p.estado_ipmadre_webPO, p.estado, CAST((julianday('now') - julianday(p.fecha_inicio_diseno)) AS INTEGER) AS dias_transc
        FROM presupuesto p
        LEFT JOIN inf_red i ON p.cod_unico = i.id
        WHERE p.prioridad IN ('GESTION 2023', 'GESTION 2024', 'EBC') AND 
            p.estado IN ('En proceso de Diseño', 'Diseño pendiente - Entidad no envia documentos/planos actualizados', 
            'Se modifica el alcance (En elab. De Nvo Diseño - Presupuesto)') """).fetchall()
    
    en_ppto = get_db().execute(
    """SELECT  i.nombre_entidad, p.cod_unico, p.ip_madre, p.bautizo, p.estado, p.eecc, CAST((julianday('now') - julianday(p.fecha_termino_diseno)) AS INTEGER) AS dias_transc
        FROM presupuesto p
        LEFT JOIN inf_red i ON p.cod_unico = i.id
        WHERE p.prioridad IN ('GESTION 2023', 'GESTION 2024', 'EBC') AND p.estado = 'Diseño Ejecutado, pdte Elab. Ppto' """).fetchall()
    
    facturado = get_db().execute(
    """SELECT  i.nombre_entidad, p.cod_unico, p.ip_madre, p.bautizo, p.estado, montoIGV
        FROM presupuesto p
        LEFT JOIN inf_red i ON p.cod_unico = i.id
        LEFT JOIN estadosOP e ON p.estado = e.estado
        WHERE p.prioridad IN ('GESTION 2023', 'GESTION 2024', 'EBC') AND e.grupo_gestion = 'FACTURADO' 
        ORDER BY e.id""").fetchall()

       
    plan_oficial_interno = get_db().execute(
        """SELECT  i.entidad, p.cod_unico, p.ip_madre, p.bautizo, p.estado, p.montoIGV, p.semana_pago_oficial, p.mes_pago_oficial, p.semana_pago_interno, p.mes_pago_planificado, CAST((julianday('now') - julianday(p.fecha_entrega_ppto)) AS INTEGER ) AS dias_transc
            FROM presupuesto p
            LEFT JOIN inf_red i ON p.cod_unico = i.id
            LEFT JOIN estadosOP e ON p.estado = e.estado
            WHERE SUBSTR(mes_pago_oficial, -1) IN ('4') 
            ORDER BY CASE p.mes_pago_oficial
                WHEN 'Enero 2024 ' THEN 0
                WHEN 'Febrero 2024' THEN 1
                WHEN 'Marzo 2024' THEN 2
                WHEN 'Abril 2024' THEN 3
                WHEN 'Mayo 2024' THEN 4
                WHEN 'Junio 2024' THEN 5
                WHEN 'Julio 2024' THEN 6
                WHEN 'Agosto 2024' THEN 7
                WHEN 'Setiembre 2024' THEN 8
                WHEN 'Octubre 2024' THEN 9
                WHEN 'Noviembre 2024' THEN 10
                WHEN 'Diciembre 2024' THEN 11
                END""").fetchall()


    sf_pago_3_meses = get_db().execute(
        """SELECT  ip_madre
            FROM presupuesto p
            LEFT JOIN estadosOP e ON p.estado = e.estado
            WHERE SUBSTR(mes_pago_oficial, -1) NOT IN ('4') AND e.grupo_gestion ='EN COORDINACIÓN' AND p.prioridad IN ('GESTION 2023', 'GESTION 2024', 'EBC') AND CAST((julianday('now') - julianday(p.fecha_entrega_ppto)) AS INTEGER)>=90""").fetchall()
    diseño_30_dias = get_db().execute(
        """SELECT  ip_madre
            FROM presupuesto 
            WHERE estado ='En proceso de Diseño' AND prioridad IN ('GESTION 2023', 'GESTION 2024', 'EBC') AND CAST((julianday('now') - julianday(fecha_inicio_diseno)) AS INTEGER )>30""").fetchall()
    ppto_4_dias = get_db().execute(
        """SELECT  ip_madre
            FROM presupuesto 
            WHERE estado ='Diseño Ejecutado, pdte Elab. Ppto' AND prioridad IN ('GESTION 2023', 'GESTION 2024', 'EBC') AND CAST((julianday('now') - julianday(fecha_termino_diseno)) AS INTEGER)>4""").fetchall()
    sin_oc_10_dias = get_db().execute(
        """SELECT  ip_madre
            FROM presupuesto 
            WHERE estado ='Diseño pendiente - IP MADRE sin orden de compra' AND prioridad IN ('GESTION 2023', 'GESTION 2024', 'EBC') AND CAST((julianday('now') - julianday(fecha_creacion_ipmadre)) AS INTEGER)>10""").fetchall()

    importante={'sin_oc_10_dias':len(sin_oc_10_dias), 'diseño_30_dias':len(sin_oc_10_dias), 'ppto_4_dias':len(ppto_4_dias), 'sf_pago_3_meses':len(sf_pago_3_meses)}
    
    observaciones = get_db().execute(
        """SELECT  h.observacion, h.fecha, h.cod_unico, p.bautizo
            FROM historial h
            LEFT JOIN presupuesto p ON h.presupuesto_id = p.id
            ORDER BY h.id DESC
            LIMIT 5""").fetchall()


    return render_template('/reportes/proyectos_gestionados_2024.html',vista_general_grupos=vista_general_grupos, vista_general=vista_general,  con_ip_sin_oc=con_ip_sin_oc, en_diseño=en_diseño, en_ppto=en_ppto, facturado=facturado, plan_oficial_interno=plan_oficial_interno, importante=importante, observaciones=observaciones)

@bp.route('/reporte/gestion_presupuestal')
@login_required
def gestion_presupuestal():
    certificados = get_db().execute(
        """ SELECT strftime('%m', validacion_oc_actual) AS 'mes', sum(monto_diseño_final) AS 'monto_final', sum(monto_inicial) AS 'monto_inicial' , avg(monto_diseño_final) AS 'monto_promedio', count(*) AS 'cant'
        FROM info_webpo
        WHERE estado_ip = 'Certificado' AND strftime('%Y', validacion_oc_actual) = '2024'
        GROUP BY strftime('%m', validacion_oc_actual) """).fetchall()
    
    certificado_por_pep = get_db().execute(
        """ SELECT SUBSTRING(pep,1,9) AS 'año_pep', sum(monto_diseño_final) AS 'monto_final', count(*) AS 'cant'
        FROM info_webpo
        WHERE estado_ip = 'Certificado' AND strftime('%Y', validacion_oc_actual) = '2024'
        GROUP BY año_pep 
        ORDER BY año_pep """).fetchall()
    
    en_certificacion = get_db().execute(
        """ SELECT sum(monto_diseño_final)
        FROM info_webpo
        WHERE estado_ip = 'En Certificación'  """).fetchall()[0][0]
    
    en_certificacion_detalle = get_db().execute(
        """ SELECT w.ip_madre AS ip_madre, r.entidad, w.monto_diseño_final, w.monto_inicial, w.solicitud_oc_actual, p.bautizo
        FROM info_webpo w
        LEFT JOIN inf_red r ON w.ip_madre = r.id
        LEFT JOIN presupuesto p ON w.ip_madre = p.ip_madre
        WHERE estado_ip = 'En Certificación'  """).fetchall()

    en_validacion_detalle = get_db().execute(
        """ SELECT w.ip_madre AS ip_madre, w.eecc, w.monto_diseño_final, w.monto_inicial, w.solicitud_oc_actual, p.bautizo, IFNULL(REPLACE(w.estado_firma, 'ATENDIDO EECC', 'PEND FIRMA ALONSO'), 'PEND EECC') AS estado_firma
        FROM info_webpo w
        LEFT JOIN presupuesto p ON w.ip_madre = p.ip_madre
        WHERE estado_ip = 'Terminado'  """).fetchall()

    pend_certificar_detalle = get_db().execute(
        """ SELECT w.ip_madre AS ip_madre, w.eecc, CAST (IFNULL(w.monto_diseño_final,0) AS INT) AS monto_diseño_final, w.monto_inicial, w.solicitud_oc_creacion , p.bautizo, w.estado_ip, p.estado
        FROM info_webpo w
        LEFT JOIN presupuesto p ON w.ip_madre = p.ip_madre
        WHERE estado_ip IN ('Diseño', 'Diseño Ejecutado') AND w.ip_madre != 'M-24-01-026'  """).fetchall()

    oc_creadas = get_db().execute(
        """ SELECT sum(monto_actual)
        FROM info_webpo
        WHERE estado_ip IN ('Terminado', 'Diseño', 'Diseño Ejecutado') AND situacion = 'OC CREADA'  """).fetchall()[0][0]
    
    con_solicitud_oc = get_db().execute(
        """ SELECT sum(w.monto_actual)
        FROM info_webpo w
        WHERE situacion IN ('SOLICITUD OC CREADA', 'SIN SOLICITUD OC') AND  strftime('%Y', solicitud_oc_creacion) = '2024' """).fetchall()[0][0]

    con_solicitud_oc_detalle = get_db().execute(
        """ SELECT w.monto_actual, w.ip_madre AS ip_madre,  w.solicitud_oc_creacion , p.bautizo, w.estado_ip
        FROM info_webpo w
        LEFT JOIN presupuesto p ON w.ip_madre = p.ip_madre
        WHERE situacion IN ('SOLICITUD OC CREADA', 'SIN SOLICITUD OC') AND  strftime('%Y', solicitud_oc_creacion) = '2024' """).fetchall()

    oc_generadas_por_estado = get_db().execute(
        """ SELECT  estado_ip, strftime('%m', validacion_oc_creacion) AS 'mes', sum(monto_inicial) AS monto, strftime('%Y', validacion_oc_creacion) AS 'año'
        FROM info_webpo
        WHERE SUBSTRING(pep, 1,9)='P-0055-24' 
        GROUP BY estado_ip, strftime('%m', validacion_oc_creacion) """).fetchall()
    
    oc_generadas_dic = {
        "Certificado": [0,0,0,0,0,0,0,0,0,0,0,0,0],
        "En Certificación": [0,0,0,0,0,0,0,0,0,0,0,0,0],
        "Terminado":[0,0,0,0,0,0,0,0,0,0,0,0,0],
        "Diseño Ejecutado":[0,0,0,0,0,0,0,0,0,0,0,0,0],
        "Diseño":[0,0,0,0,0,0,0,0,0,0,0,0,0],
        "Registrado":[0,0,0,0,0,0,0,0,0,0,0,0,0],
        "Cancelado":[0,0,0,0,0,0,0,0,0,0,0,0,0]
    }

    total_generadas = 0
    for i in oc_generadas_por_estado:
        if i['año'] == '2023':
            oc_generadas_dic[i['estado_ip']][0] = i['monto']+ oc_generadas_dic[i['estado_ip']][0]
        else:
            oc_generadas_dic[i['estado_ip']][int(i['mes'])] = i['monto'] + oc_generadas_dic[i['estado_ip']][int(i['mes'])]
        total_generadas = total_generadas + i['monto']

    oc_generadas_dic = json.dumps(oc_generadas_dic)
    


    if en_certificacion is None:
        en_certificacion=0
    if con_solicitud_oc is None:
        con_solicitud_oc=0

    cert_cant = {'01': 0, '02': 0, '03': 0, '04': 0, '05':0, '06':0, '07':0, '08':0, '09':0, '10':0, '11': 0, '12':0}
    cert_monto_ini = {'01': 0, '02': 0, '03': 0, '04': 0, '05':0, '06':0, '07':0, '08':0, '09':0, '10':0, '11': 0, '12':0}
    cert_monto_fin = {'01': 0, '02': 0, '03': 0, '04': 0, '05':0, '06':0, '07':0, '08':0, '09':0, '10':0, '11': 0, '12':0}
    cert_monto_prom = {'01': 0, '02': 0, '03': 0, '04': 0, '05':0, '06':0, '07':0, '08':0, '09':0, '10':0, '11': 0, '12':0}
    
    for i in certificados:
        cert_cant[i['mes']] = i['cant']
        cert_monto_ini[i['mes']] = i['monto_inicial']
        cert_monto_fin[i['mes']] = i['monto_final']
        cert_monto_prom[i['mes']] = i['monto_promedio']
    cant_cert = list(cert_cant.values())
    monto_ini_cert = list(cert_monto_ini.values())
    monto_fin_cert = list(cert_monto_fin.values())
    monto_prom_cert = list(cert_monto_prom.values())


    ppto_habilitado = sum(monto_fin_cert) + en_certificacion + oc_creadas

    total_generadas = abreviaNumero(total_generadas)
    prom_certificacion = abreviaNumero(monto_prom_cert)
    certificado = abreviaNumero(monto_fin_cert)
    en_certificacion = abreviaNumero(en_certificacion)
    oc_creadas = abreviaNumero(oc_creadas)
    con_solicitud_oc = abreviaNumero(con_solicitud_oc)
    ppto_habilitado = abreviaNumero(ppto_habilitado)

    
    return render_template('/reportes/gestion_presupuestal.html',  certificado_por_pep=certificado_por_pep, con_solicitud_oc_detalle=con_solicitud_oc_detalle ,oc_generadas_dic=oc_generadas_dic,  prom_certificacion=prom_certificacion, pend_certificar_detalle=pend_certificar_detalle, en_validacion_detalle=en_validacion_detalle, en_certificacion_detalle=en_certificacion_detalle, cant_cert=cant_cert, monto_ini_cert=monto_ini_cert, monto_fin_cert=monto_fin_cert, monto_prom_cert=monto_prom_cert, ppto_habilitado = ppto_habilitado, total_generadas=total_generadas,  con_solicitud_oc=con_solicitud_oc, certificado=certificado, en_certificacion=en_certificacion, oc_creadas=oc_creadas)
    
    
@bp.route('/reporte/tiempos_inf_red')
@login_required
def tiempos_inf_red():       
    ingresadas = get_db().execute(
        """ SELECT count(estado_inf_red)
        FROM inf_red
        WHERE strftime('%Y', fecha_correo) = '2024'""").fetchall()[0][0]

    atendidas_por_mes = get_db().execute(
        """ SELECT strftime('%m', fecha_correo) AS mes, count(*) AS cant, avg(CAST((julianday(fecha_respuesta) - julianday(fecha_correo)) AS INTEGER)) AS prom
            FROM inf_red
            WHERE strftime('%Y', fecha_correo) = '2024' AND estado_inf_red = 'ATENDIDO' 
            GROUP BY strftime('%m', fecha_correo)""").fetchall()
    meses_cant = {'01': 0, '02': 0, '03': 0, '04': 0, '05':0, '06':0, '07':0, '08':0, '09':0, '10':0, '11': 0, '12':0}
    meses_prom = {'01': 0, '02': 0, '03': 0, '04': 0, '05':0, '06':0, '07':0, '08':0, '09':0, '10':0, '11': 0, '12':0}
    for i in atendidas_por_mes:
        meses_cant[i['mes']] = i['cant']
        meses_prom[i['mes']] = i['prom']
    cant_mes = list(meses_cant.values())
    prom_mes = list(meses_prom.values())

    atendidas = sum(cant_mes)

    sin_inter = get_db().execute(
        """ SELECT  count(*)
            FROM inf_red i 
            LEFT JOIN  presupuesto p ON i.id=p.cod_unico
            WHERE strftime('%Y', fecha_correo) = '2024' AND estado_inf_red = 'ATENDIDO' AND p.id IS NULL """).fetchall()[0][0]
    con_inter = atendidas - sin_inter

    ips_con_inter = get_db().execute(
        """ SELECT  e.agrupacion_etapas, count(*)
            FROM inf_red i 
            LEFT JOIN  presupuesto p ON i.id=p.cod_unico
            LEFT JOIN  estadosOP e ON p.estado=e.estado
            WHERE strftime('%Y', fecha_correo) = '2024' AND estado_inf_red = 'ATENDIDO' AND p.id IS NOT NULL 
            GROUP BY e.agrupacion_etapas""").fetchall()
    estados,cant = zip(*ips_con_inter)
    estados_con_inter=','.join(estados)
    cant_con_inter=list(cant)


    tma_info_red, tma_oc, tma_diseño, tma_ppto, tma_coordinacion, tma_total = tmas()


    
    return render_template('/reportes/tiempos_inf_red.html',  ingresadas=ingresadas, atendidas=atendidas, tma_info_red=tma_info_red, cant_mes=cant_mes, prom_mes=prom_mes, sin_inter=sin_inter, con_inter=con_inter, estados_con_inter=estados_con_inter, cant_con_inter=cant_con_inter, tma_diseño=tma_diseño, tma_ppto=tma_ppto, tma_coordinacion=tma_coordinacion, tma_oc=tma_oc, tma_total=tma_total)

@bp.route('/reporte/tiempos_diseño')
@login_required
def tiempos_diseño():
    ejecutados_por_mes = get_db().execute(
        """ SELECT strftime('%m',fecha_termino_diseno) AS mes, count(*) AS cant, sum(montoIGV) AS monto,  avg(CAST((julianday(fecha_termino_diseno) - julianday(fecha_inicio_diseno)) AS INTEGER)) AS prom
        FROM presupuesto
        WHERE strftime('%Y', fecha_creacion) = '2024' AND (strftime('%Y',fecha_entrega_ppto) = '2024' OR strftime('%Y',fecha_termino_diseno) = '2024') 
        GROUP BY strftime('%m',fecha_termino_diseno) """).fetchall()
    meses_cant = {'01': 0, '02': 0, '03': 0, '04': 0, '05':0, '06':0, '07':0, '08':0, '09':0, '10':0, '11': 0, '12':0}
    meses_prom = {'01': 0, '02': 0, '03': 0, '04': 0, '05':0, '06':0, '07':0, '08':0, '09':0, '10':0, '11': 0, '12':0}
    meses_monto = {'01': 0, '02': 0, '03': 0, '04': 0, '05':0, '06':0, '07':0, '08':0, '09':0, '10':0, '11': 0, '12':0}
    for i in ejecutados_por_mes:
        meses_cant[i['mes']] = i['cant']
        meses_prom[i['mes']] = i['prom']
        meses_monto[i['mes']] = i['monto']
    cant_mes = list(meses_cant.values())
    prom_mes = list(meses_prom.values())
    monto_mes = list(meses_monto.values())

    ejecutados = sum(cant_mes)
    if sum(monto_mes)>1000000:
        ejecutados_monto = str(round(sum(monto_mes)/1000000,1))+' MM'
    elif sum(monto_mes)>1000:
         ejecutados_monto = str(round(sum(monto_mes)/1000,1))+' K'
    else:
        ejecutados_monto = round(sum(monto_mes),1)

    estado_actual = get_db().execute(
        """ SELECT  e.agrupacion_etapas, count(*), sum(montoIGV)
            FROM presupuesto p 
            LEFT JOIN  estadosOP e ON p.estado=e.estado
            WHERE strftime('%Y', fecha_creacion) = '2024' AND (strftime('%Y',fecha_entrega_ppto) = '2024' OR strftime('%Y',fecha_termino_diseno) = '2024') 
            GROUP BY e.agrupacion_etapas""").fetchall()
    estados,cant,monto = zip(*estado_actual)
    estados_str=','.join(estados)
    cant_estados=list(cant)
    monto_estados=list(monto)

    tma_info_red, tma_oc, tma_diseño, tma_ppto, tma_coordinacion, tma_total = tmas()

    return render_template('/reportes/tiempos_diseño.html', ejecutados_por_mes=ejecutados_por_mes, ejecutados=ejecutados, cant_mes=cant_mes, prom_mes=prom_mes, monto_mes=monto_mes, ejecutados_monto=ejecutados_monto, tma_diseño=tma_diseño, estados_str=estados_str, cant_estados=cant_estados, monto_estados=monto_estados, tma_info_red=tma_info_red, tma_ppto=tma_ppto, tma_coordinacion=tma_coordinacion, tma_oc=tma_oc, tma_total=tma_total)

@bp.route('/reporte/tiempos_presupuesto')
@login_required
def tiempos_presupuesto():
    emitidos_por_mes = get_db().execute(
        """ SELECT strftime('%m',fecha_entrega_ppto) AS mes, count(*) AS cant, sum(montoIGV) AS monto,  avg(CAST((julianday(fecha_entrega_ppto) - julianday(fecha_termino_diseno)) AS INTEGER)) AS prom
        FROM presupuesto
        WHERE strftime('%Y', fecha_creacion) = '2024' AND strftime('%Y',fecha_entrega_ppto) = '2024' 
        GROUP BY strftime('%m',fecha_entrega_ppto) """).fetchall()
    meses_cant = {'01': 0, '02': 0, '03': 0, '04': 0, '05':0, '06':0, '07':0, '08':0, '09':0, '10':0, '11': 0, '12':0}
    meses_prom = {'01': 0, '02': 0, '03': 0, '04': 0, '05':0, '06':0, '07':0, '08':0, '09':0, '10':0, '11': 0, '12':0}
    meses_monto = {'01': 0, '02': 0, '03': 0, '04': 0, '05':0, '06':0, '07':0, '08':0, '09':0, '10':0, '11': 0, '12':0}
    for i in emitidos_por_mes:
        meses_cant[i['mes']] = i['cant']
        meses_prom[i['mes']] = i['prom']
        meses_monto[i['mes']] = i['monto']
    cant_mes = list(meses_cant.values())
    prom_mes = list(meses_prom.values())
    monto_mes = list(meses_monto.values())

    emitidos = sum(cant_mes)
    if sum(monto_mes)>1000000:
        emitidos_monto = str(round(sum(monto_mes)/1000000,1))+' MM'
    elif sum(monto_mes)>1000:
         emitidos_monto = str(round(sum(monto_mes)/1000,1))+' K'
    else:
        emitidos_monto = round(sum(monto_mes),1)

    estado_actual = get_db().execute(
        """ SELECT  e.agrupacion_etapas, count(*), sum(montoIGV)
            FROM presupuesto p 
            LEFT JOIN  estadosOP e ON p.estado=e.estado
            WHERE strftime('%Y', fecha_creacion) = '2024' AND strftime('%Y',fecha_entrega_ppto) = '2024'
            GROUP BY e.agrupacion_etapas""").fetchall()
    estados,cant,monto = zip(*estado_actual)
    estados_str=','.join(estados)
    cant_estados=list(cant)
    monto_estados=list(monto)

    tma_info_red, tma_oc, tma_diseño, tma_ppto, tma_coordinacion, tma_total = tmas()

    return render_template('/reportes/tiempos_presupuesto.html', emitidos_por_mes=emitidos_por_mes, emitidos=emitidos, cant_mes=cant_mes, prom_mes=prom_mes, monto_mes=monto_mes, emitidos_monto=emitidos_monto, tma_ppto=tma_ppto, estados_str=estados_str, cant_estados=cant_estados, monto_estados=monto_estados, tma_info_red=tma_info_red,  tma_diseño=tma_diseño, tma_coordinacion=tma_coordinacion, tma_oc=tma_oc, tma_total=tma_total)

@bp.route('/reporte/tiempos_coordinacion')
@login_required
def tiempos_coordinacion():
    pagados_por_mes = get_db().execute(
        """ SELECT REPLACE(REPLACE(REPLACE(estado,'Pagado',''),'2023',''),' ','') AS mes, count(*) AS cant, sum(montoIGV) AS monto,  avg(CAST((julianday(fecha_firma_convenio) - julianday(fecha_entrega_ppto)) AS INTEGER )) AS prom
        FROM presupuesto
        WHERE SUBSTR(estado,1,6)='Pagado' AND SUBSTR(estado,-1)='3' 
        GROUP BY mes """).fetchall()
    meses_cant = {'Enero': 0, 'Febrero': 0, 'Marzo': 0, 'Abril': 0, 'Mayo':0, 'Junio':0, 'Julio':0, 'Agosto':0, 'Setiembre':0, 'Octubre':0, 'Noviembre': 0, 'Diciembre':0}
    meses_prom = {'Enero': 0, 'Febrero': 0, 'Marzo': 0, 'Abril': 0, 'Mayo':0, 'Junio':0, 'Julio':0, 'Agosto':0, 'Setiembre':0, 'Octubre':0, 'Noviembre': 0, 'Diciembre':0}
    meses_monto = {'Enero': 0, 'Febrero': 0, 'Marzo': 0, 'Abril': 0, 'Mayo':0, 'Junio':0, 'Julio':0, 'Agosto':0, 'Setiembre':0, 'Octubre':0, 'Noviembre': 0, 'Diciembre':0}
    for i in pagados_por_mes:
        if i['cant'] is not None:
            meses_cant[i['mes']] = i['cant']
        if i['prom'] is not None:
            meses_prom[i['mes']] = i['prom']
        if i['monto'] is not None:
            meses_monto[i['mes']] = i['monto']
        
        
        
        
            
    cant_mes = list(meses_cant.values())
    prom_mes = list(meses_prom.values())
    monto_mes = list(meses_monto.values())

    pagados = sum(cant_mes)
    if sum(monto_mes)>1000000:
        pagados_monto = str(round(sum(monto_mes)/1000000,1))+' MM'
    elif sum(monto_mes)>1000:
         pagados_monto = str(round(sum(monto_mes)/1000,1))+' K'
    else:
        pagados_monto = round(sum(monto_mes),1)

    oc_ejecucion = get_db().execute(
        """ SELECT  e.agrupacion_etapas, count(*), sum(montoIGV)
            FROM presupuesto p 
            LEFT JOIN  estadosOP e ON p.estado=e.estado
            WHERE SUBSTR(p.estado,1,6)='Pagado' AND SUBSTR(p.estado,-1)='3'
            GROUP BY e.agrupacion_etapas""").fetchall()
    estados,cant,monto = zip(*oc_ejecucion)
    estados_str=','.join(estados)
    cant_estados=list(cant)
    monto_estados=list(monto)

    tma_info_red, tma_oc, tma_diseño, tma_ppto, tma_coordinacion, tma_total = tmas()

    return render_template('/reportes/tiempos_coordinacion.html', pagados_por_mes=pagados_por_mes, pagados=pagados, cant_mes=cant_mes, prom_mes=prom_mes, monto_mes=monto_mes, pagados_monto=pagados_monto, tma_coordinacion=tma_coordinacion, estados_str=estados_str, cant_estados=cant_estados, monto_estados=monto_estados, tma_info_red=tma_info_red, tma_ppto=tma_ppto, tma_diseño=tma_diseño, tma_oc=tma_oc, tma_total=tma_total)

@bp.route('/reporte/exportar')
@login_required
def export():
    return render_template('/reportes/exportar.html')

@bp.route('/reporte/desestimados')
@login_required
def desestimados():
    desestimados = get_db().execute(
        """ SELECT p.ip_madre, p.estado, p.bautizo, i.entidad
        FROM presupuesto p
        LEFT JOIN  estadosOP e ON p.estado=e.estado
        LEFT JOIN  inf_red i ON p.cod_unico=i.id
        WHERE e.grupo_gestion='FACTURADO' """).fetchall()
    motivos = get_db().execute(
        """ SELECT p.estado, count(*), sum(montoIGV)
        FROM presupuesto p
        LEFT JOIN  estadosOP e ON p.estado=e.estado
        LEFT JOIN  inf_red i ON p.cod_unico=i.id
        WHERE e.grupo_gestion='FACTURADO' 
        GROUP BY p.estado""").fetchall()

    estados,cant,monto = zip(*motivos)
    estados_str=','.join(estados)
    cant_estados=list(cant)
    monto_estados=list(monto)

    return render_template('/reportes/desestimados.html', desestimados=desestimados, estados_str=estados_str, cant_estados=cant_estados, monto_estados=monto_estados)

@bp.route('/download_inf_red')
def download_inf_red():
    data_base = get_db().execute(
        """
        SELECT id AS "Código Único", proyecto AS "Proyecto", entidad AS 'Entidad'
        , fecha_documento ,  fecha_correo ,  departamento,  provincia ,
        distrito ,   resumen_planta ,   fecha_respuesta ,  estado_inf_red, estado_proyecto,tma   
        FROM inf_red
        """
        
    )

    data = data_base.fetchall()
    columns = [desc[0] for desc in data_base.description]
    df = pd.DataFrame(list(data), columns=columns)
    df.to_excel("inf_red.xlsx", startcol=0, index=False)
    return send_file("../inf_red.xlsx", as_attachment=True)


@bp.route('/download_presupuestos')
def download_presupuestos():
    data_base = get_db().execute(
        """
        SELECT 
        cod_unico AS "Codigo Unico",
        DATE(fecha_creacion) AS "Fecha creacion",
        bautizo AS "Bautizo",
        documento AS "Documento",
        fecha_documento AS "Fecha Documento",
        contacto AS "Contacto",
        correo_contacto AS "Correo Contacto",
        telefono_contacto AS "Telefono Contacto",
        ip_madre AS "IP Madre",
        fecha_creacion_ipmadre AS "Fecha Creacion IP",
        estado_ipmadre_webPO AS "Estado WebPO",
        eecc AS "EECC",
        solicitudOC AS "Solicitud OC",
        fecha_inicio_diseno AS "Fecha Inicio Diseño",
        fecha_termino_diseno AS "Fecha Termino Diseño",
        fecha_entrega_ppto AS "Fecha Entrega PPTO",
        nro_ppto AS "Nro PPTO",
        montoIGV AS "Monto IGV",
        prioridad AS "Prioridad",
        p.estado AS "Estado",
        e.grupo_gestion AS "Grupo Gestion",
        mes_pago_planificado AS "Mes Interno Pago",
        mes_pago_oficial AS "Mes Oficial Pago",
        semana_pago_interno AS "Sem Interna Pago",
        semana_pago_oficial AS "Sem Oficial Pago"
       
        FROM presupuesto p
        LEFT JOIN estadosOP e ON p.estado = e.estado
        """
        
    )

    data = data_base.fetchall()
    columns = [desc[0] for desc in data_base.description]
    df = pd.DataFrame(list(data), columns=columns)
    df.to_excel("presupuestos.xlsx", startcol=0, index=False)
    return send_file("../presupuestos.xlsx", as_attachment=True)


@bp.route('/download_convenios')
def download_convenios():
    data_base = get_db().execute(
        """SELECT 
        cod_unico AS "Codigo Unico",
        bautizo AS "Bautizo",
        ip_madre AS "IP Madre",
        montoIGV AS "Monto IGV",
        prioridad AS "Prioridad",
        estado AS "Estado",
        nro_convenio AS "Nro Convenio",
        fecha_firma_convenio AS "Fecha Firma Conv.",
        plazo_convenio AS "Plazo Conv.",
        tiempo AS "Tiempo Conv.",
        fecha_caducidad AS "Fecha Caducidad Conv.",
        numero_factura AS "Nro Factura",
        fecha_pago_96 AS "Fecha Pago 96%",
        fecha_pago_4 AS "Fecha Pago 4%"
       
        FROM presupuesto"""
        
    )

    data = data_base.fetchall()
    columns = [desc[0] for desc in data_base.description]
    df = pd.DataFrame(list(data), columns=columns)
    df.to_excel("convenios.xlsx", startcol=0, index=False)
    return send_file("../convenios.xlsx", as_attachment=True)

@bp.route('/download_info_webpo')
def download_info_webpo():
    data_base = get_db().execute(
        """SELECT 
        *
       
        FROM info_webpo"""
        
    )

    data = data_base.fetchall()
    columns = [desc[0] for desc in data_base.description]
    df = pd.DataFrame(list(data), columns=columns)
    df.to_excel("info_webpo.xlsx", startcol=0, index=False)
    return send_file("../info_webpo.xlsx", as_attachment=True)

def tmas():
    tma_info_red = get_db().execute(
        """ SELECT CAST(avg(CAST((julianday(fecha_respuesta) - julianday(fecha_correo)) AS INTEGER)) AS INT)
        FROM inf_red
        WHERE strftime('%Y', fecha_correo) = '2024' AND estado_inf_red = 'ATENDIDO' """).fetchall()[0][0] 
    tma_oc = 25 
    
    tma_diseño = get_db().execute(
        """ SELECT CAST (avg(CAST( (julianday(fecha_termino_diseno) - julianday(fecha_inicio_diseno)) AS INTEGER ) ) AS INT )
        FROM presupuesto
        WHERE strftime('%Y', fecha_creacion) = '2024' AND (strftime('%Y',fecha_entrega_ppto) = '2024' OR strftime('%Y',fecha_termino_diseno) = '2024') """).fetchall()[0][0]
    tma_ppto = get_db().execute(
        """ SELECT CAST (avg(CAST( (julianday(fecha_entrega_ppto) - julianday(fecha_termino_diseno)) AS INTEGER ) ) AS INT )
        FROM presupuesto
        WHERE strftime('%Y', fecha_creacion) = '2024' AND strftime('%Y',fecha_entrega_ppto) = '2024' """).fetchall()[0][0]
    tma_coordinacion = get_db().execute(
        """ SELECT CAST (avg(CAST( (julianday(fecha_firma_convenio) - julianday(fecha_entrega_ppto)) AS INTEGER ) ) AS INT )
        FROM presupuesto
        WHERE SUBSTR(estado,1,6)='Pagado' AND SUBSTR(estado,-1)='3'  """).fetchall()[0][0]
    tma_ppto = 8    
    
    tma_total=tma_info_red+tma_oc+tma_ppto+tma_coordinacion

    
    return [tma_info_red, tma_oc, tma_diseño, tma_ppto, tma_coordinacion,tma_total]


def abreviaNumero(monto):
    if isinstance(monto, list):
        if sum(monto)>1000000:
            return str(round(sum(monto)/1000000,1))+' MM'
        elif sum(monto)>1000:
            return str(round(sum(monto)/1000,1))+' K'
        else:
            return round(sum(monto),1)
    else:
        if monto>1000000:
            return str(round(monto/1000000,1))+' MM'
        elif monto>1000:
            return str(round(monto/1000,1))+' K'
        else:
            return round(monto,1)