dict_colores = {
    'ProcesoInfRed': '#80D8FF',
    'InfRedEnviado': '#255684',
    'Cancelado': '#FF0000',
    'GenerarIP': '#7f6fbd',
    'PendienteOC': '#b87e40',
    'Diseno': '#9B870D',
    'Presupuesto': '#7851A9',
    'Convenio': '#006400',
    'PendPago': '#40b878',
    'Pagado': '#2acc1f'
}

def get_color_estado(estado):
    color = ''
    if estado == 'En proceso de Información de Red':
        color = dict_colores['ProcesoInfRed']
    elif estado == 'Información de Red enviado a Entidad':
        color = dict_colores['InfRedEnviado']
    elif estado == 'Generar IP Madre':
        color = dict_colores['GenerarIP']
    elif estado == 'Pendiente OC de Diseño':
        color = dict_colores['PendienteOC']
    elif estado in ['En proceso de Diseño', 'Pendiente respuesta de la Entidad - Diseño']:
        color = dict_colores['Diseno']
    elif estado in ['En proceso de Presupuesto', 'Pendiente respuesta de la Entidad - Presupuesto']:
        color = dict_colores['Presupuesto']
    elif estado in ['En proceso de Convenio', 'Pendiente respuesta de la Entidad - Convenio']:
        color = dict_colores['Convenio']
    elif estado == 'En proceso de Pago':
        color = dict_colores['PendPago']
    elif estado == 'Pagado por Entidad':
        color = dict_colores['Pagado']
    elif estado in ['Cancelado - Solo pedido de Información de Red', 'Cancelado - No existe interferencia', 
                    'Cancelado - No acepta Presupuesto', 'Cancelado - No acepta Convenio', 'Cancelado - En gestión con otro IP Madre', 
                    'Cancelado - Cambio de Gestión', 'Cancelado - Anulado a pedido de la Entidad', 'Cancelado - Ejecutado por mantenimiento', 
                    'Derivar a Relaciones Institucionales', 'Información de Red Cancelada', 'Diseño con Reparos']:
        color = dict_colores['Cancelado']
    else:
        color = 'blue'
        
    return color

def get_estado_grupo_infred(estado):
    estado_general = ['En proceso de Información de Red']
    if estado == 'PENDIENTE' or estado == 'EN PROCESO':
        estado_general = ['En proceso de Información de Red']
    elif estado == 'ATENDIDO':
        estado_general = ['Información de Red enviado a Entidad']
    elif estado == 'CANCELADO':
        estado_general = ['Información de Red Cancelada']
    return estado_general

#Funcion para obtener la clase para la línea de tiempo de ViewAll
def get_estado_grupo_class(estado_grupo):
    list_class_all = []
    for estado in estado_grupo:
        list_class = []
        # Paso 1
        if estado == "En proceso de Información de Red":
            list_class.append(["En proceso de <br>Información de Red", "step-wizard-item current-item"])
        else:
            list_class.append(["En proceso de <br>Información de Red", "step-wizard-item"])
        # Paso 2
        if estado == "Información de Red enviado a Entidad":
            list_class.append(["Información de Red <br>enviado a Entidad", "step-wizard-item current-item"])
        elif estado == "Información de Red Cancelada":
            list_class.append(["Información de Red <br>Cancelada", "step-wizard-item current-item"])
        else:
            list_class.append(["Información de Red <br>enviado a Entidad", "step-wizard-item"])
        # Paso 3
        if estado == "Generar IP Madre":
            list_class.append(["Generar IP Madre", "step-wizard-item current-item"])
        elif estado == "Cancelado - Solo pedido de Información de Red":
            list_class.append(["Cancelado", "step-wizard-item current-item"])
        else:
            list_class.append(["Generar IP Madre", "step-wizard-item"])
        # Paso 4
        if estado == "Pendiente OC de Diseño":
            list_class.append(["Pendiente OC de Diseño", "step-wizard-item current-item"])
        else:
            list_class.append(["Pendiente OC de Diseño", "step-wizard-item"])
        # Paso 5
        if estado == "En proceso de Diseño":
            list_class.append(["En proceso de Diseño", "step-wizard-item current-item"])
        elif estado == "Pendiente respuesta de la Entidad - Diseño":
            list_class.append(["Pendiente respuesta<br>de la Entidad", "step-wizard-item current-item"])
        elif estado == "Diseño con Reparos":
            list_class.append(["Diseño con Reparos", "step-wizard-item current-item"])
        elif estado == "Cancelado - No existe interferencia":
            list_class.append(["Cancelado", "step-wizard-item current-item"])
        else:
            list_class.append(["En proceso de Diseño", "step-wizard-item"])
        # Paso 6
        if estado == "En proceso de Presupuesto":
            list_class.append(["En proceso de Presupuesto", "step-wizard-item current-item"])
        elif estado == "Pendiente respuesta de la Entidad - Presupuesto":
            list_class.append(["Pendiente respuesta<br>de la Entidad", "step-wizard-item current-item"])
        elif estado in ["Cancelado - No acepta Presupuesto", "Cancelado - En gestión con otro IP Madre", 
                        "Cancelado - Cambio de Gestión", "Cancelado - Anulado a pedido de la Entidad", "Cancelado - Ejecutado por mantenimiento"]:
            list_class.append(["Cancelado", "step-wizard-item current-item"])
        else:
            list_class.append(["En proceso de Presupuesto", "step-wizard-item"])
        # Paso 7
        if estado == "En proceso de Convenio":
            list_class.append(["En proceso de Convenio", "step-wizard-item current-item"])
        elif estado == "Pendiente respuesta de la Entidad - Convenio":
            list_class.append(["Pendiente respuesta<br>de la Entidad", "step-wizard-item current-item"])
        elif estado == "Derivar a Relaciones Institucionales":
            list_class.append(["Derivar a Relaciones<br>Institucionales", "step-wizard-item current-item"])
        elif estado in ["Cancelado - No acepta Convenio", "Cancelado - Ejecutado por mantenimiento"]:
            list_class.append(["Cancelado", "step-wizard-item current-item"])
        else:
            list_class.append(["En proceso de Convenio", "step-wizard-item"])
        # Paso 8
        if estado == "En proceso de Pago":
            list_class.append(["En proceso de Pago", "step-wizard-item current-item"])
        else:
            list_class.append(["En proceso de Pago", "step-wizard-item"])
        # Paso 9
        if estado == "Pagado por Entidad":
            list_class.append(["Pagado por Entidad", "step-wizard-item current-item"])
        else:
            list_class.append(["Pagado por Entidad", "step-wizard-item"])
        
        list_class_all.append(list_class)

    return list_class_all