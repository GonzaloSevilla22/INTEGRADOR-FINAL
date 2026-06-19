"""
Modelos de la aplicación.
Importar en orden: tablas intermedias → Categoria → Producto → Ingrediente → Usuarios/Pedidos.
"""

# Tablas intermedias (sin dependencias circulares internas)
from app.models.producto_categoria import ProductoCategoria  # noqa: F401
from app.models.producto_ingrediente import ProductoIngrediente  # noqa: F401
from app.models.usuario_rol import UsuarioRol  # noqa: F401
from app.models.ingrediente import Ingrediente  # noqa: F401

# Entidades principales (dependen de tablas intermedias)
from app.models.categoria import Categoria  # noqa: F401
from app.models.producto import Producto  # noqa: F401
from app.models.rol import Rol  # noqa: F401
from app.models.usuario import Usuario  # noqa: F401
from app.models.direccion_entrega import DireccionEntrega  # noqa: F401
from app.models.estado_pedido import EstadoPedido  # noqa: F401
from app.models.forma_pago import FormaPago  # noqa: F401
from app.models.pedido import Pedido  # noqa: F401
from app.models.detalle_pedido import DetallePedido  # noqa: F401
from app.models.historial_estado_pedido import HistorialEstadoPedido  # noqa: F401
from app.models.pago import Pago  # noqa: F401
from app.models.unidad_medida import UnidadMedida  # noqa: F401

__all__ = [
    "Categoria",
    "Producto",
    "Ingrediente",
    "ProductoCategoria",
    "ProductoIngrediente",
    "Rol",
    "Usuario",
    "UsuarioRol",
    "DireccionEntrega",
    "EstadoPedido",
    "FormaPago",
    "Pedido",
    "DetallePedido",
    "HistorialEstadoPedido",
    "Pago",
    "UnidadMedida",
]
