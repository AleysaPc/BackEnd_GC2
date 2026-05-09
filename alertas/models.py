# alertas/models.py
from django.db import models
from django.utils import timezone

class AlertaVencimiento(models.Model):
    TIPO_ALERTA_CHOICES = [
        ("por_vencer", "Por vencer"),
        ("vencido", "Vencido"),
    ]
    NIVEL_ALERTA_CHOICES = [ 
       ("informativa", "Informativa"),
       ("preventiva", "Preventiva"),
       ("critica", "Crítica"),
    ]
    
    #ForeignKey real para integridad referencial 
        #Correspondencia nombre del campo
        #models.ForeignKey(...) Esto define una relación muchos a uno (Many to One)
        #correspondencia.Correspondencia --> indica a que modelo esta apuntando nombre de la app y nombre del modelo
        #on_delete=models.CASCADE -> (Define que pasa cuando se elimina la correspondencia) CASCADE -->Eliminas una correspondencia automaticamente se elimina las alertas relaiconadas
        #related_name permite acceder de manera más sencillas a los datos. 
    correspondencia = models.ForeignKey(
        "correspondencia.Correspondencia", on_delete=models.CASCADE, related_name="alertas", null=True, blank=True
    )
    usuario_responsable = models.ForeignKey(
        "usuario.CustomUser", on_delete=models.CASCADE, related_name="alertas_usuario"
    )
    tipo_alerta = models.CharField(max_length=25, choices=TIPO_ALERTA_CHOICES)
    nivel_alerta = models.CharField(max_length=11, choices=NIVEL_ALERTA_CHOICES, default="informativa")
    
    fecha_alerta = models.DateTimeField(auto_now_add=True)
    vista = models.BooleanField(default=False)
    fecha_vista = models.DateTimeField(null=True, blank=True)
    
    #class Meta define opciones adicionales para el modelo
    class Meta:
        ordering = ['-fecha_alerta'] #Orden por defecto el - define orden descendiente
        indexes = [
            #Como indice de libro par busquedas 
            models.Index(fields=['usuario_responsable','vista']),
            models.Index(fields=['tipo_alerta']),
        ]
        constraints = [ #Evita duplicados.
            models.UniqueConstraint(
                fields=['correspondencia', 'usuario_responsable', 'tipo_alerta'],
                name='unique_alerta_correspondencia_usuario_tipo'
            )
        ]
    #Métodos
    def marcar_como_vista(self):
        if not self.vista:
            self.vista = True
            self.fecha_vista = timezone.now()
            self.save(update_fields=['vista', 'fecha_vista'])
    
    #Método
    def get_color_estado(self):
        """Retorna el color según el tipo de alerta"""
        colores = {
            'asignacion': '🔵',
            'por_vencer': '🟡',  
            'vencido': '🔴',
        }
        return colores.get(self.tipo_alerta, '⚪')
        