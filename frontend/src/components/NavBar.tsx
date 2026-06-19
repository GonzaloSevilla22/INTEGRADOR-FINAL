import { useState } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function NavBar(): JSX.Element {
  const { logout, isAdmin, isClient, isStock, isPedidos, user } = useAuth();
  const [open, setOpen] = useState(false);

  return (
    <header className="border-b border-orange-100 bg-white/90 shadow-sm backdrop-blur">
      <div className="mx-auto max-w-6xl px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setOpen(!open)}
              className="rounded border border-orange-200 bg-orange-50 px-3 py-2 text-sm font-medium text-orange-900 hover:bg-orange-100"
            >
              ☰ Menú
            </button>
            <span className="text-sm font-semibold text-orange-700">Food Store</span>
            {user && (
              <span className="ml-4 text-sm text-slate-600">
                {user.nombre} {user.apellido}
              </span>
            )}
          </div>
          {user ? (
            <button
              type="button"
              onClick={logout}
              className="rounded bg-orange-500 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-orange-600"
            >
              Logout
            </button>
          ) : (
            <NavLink
              to="/login"
              className="rounded bg-orange-500 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-orange-600"
            >
              Ingresar
            </NavLink>
          )}
        </div>

        {open && (
          <nav className="mt-4 flex flex-wrap gap-2">
            <NavLink
              to="/home"
              className={({ isActive }) =>
                `rounded px-3 py-2 text-sm ${isActive ? "bg-orange-500 text-white" : "bg-orange-100 text-orange-900 hover:bg-orange-200"}`
              }
            >
              🏠 Home
            </NavLink>

            <NavLink
              to="/productos"
              className={({ isActive }) =>
                `rounded px-3 py-2 text-sm ${isActive ? "bg-orange-500 text-white" : "bg-orange-100 text-orange-900 hover:bg-orange-200"}`
              }
            >
              🛍️ Productos
            </NavLink>

            {!isAdmin && !isPedidos && !isStock && (
              <NavLink
                to="/carrito"
                className={({ isActive }) =>
                  `rounded px-3 py-2 text-sm ${isActive ? "bg-orange-500 text-white" : "bg-orange-100 text-orange-900 hover:bg-orange-200"}`
                }
              >
                🛒 Carrito
              </NavLink>
            )}

            {isClient && (
              <>
                <NavLink
                  to="/mis-pedidos"
                  className={({ isActive }) =>
                    `rounded px-3 py-2 text-sm ${isActive ? "bg-orange-500 text-white" : "bg-orange-100 text-orange-900 hover:bg-orange-200"}`
                  }
                >
                  📦 Mis Pedidos
                </NavLink>
                <NavLink
                  to="/perfil"
                  className={({ isActive }) =>
                    `rounded px-3 py-2 text-sm ${isActive ? "bg-orange-500 text-white" : "bg-orange-100 text-orange-900 hover:bg-orange-200"}`
                  }
                >
                  👤 Perfil
                </NavLink>
              </>
            )}

            {isAdmin && (
              <>
                <NavLink
                  to="/categorias"
                  className={({ isActive }) =>
                    `rounded px-3 py-2 text-sm ${isActive ? "bg-orange-500 text-white" : "bg-orange-100 text-orange-900 hover:bg-orange-200"}`
                  }
                >
                  📂 Categorías
                </NavLink>
                <NavLink
                  to="/ingredientes"
                  className={({ isActive }) =>
                    `rounded px-3 py-2 text-sm ${isActive ? "bg-orange-500 text-white" : "bg-orange-100 text-orange-900 hover:bg-orange-200"}`
                  }
                >
                  🧂 Ingredientes
                </NavLink>
                <NavLink
                  to="/ventas"
                  className={({ isActive }) =>
                    `rounded px-3 py-2 text-sm ${isActive ? "bg-orange-500 text-white" : "bg-orange-100 text-orange-900 hover:bg-orange-200"}`
                  }
                >
                  💰 Ventas
                </NavLink>

                <NavLink
                  to="/usuarios"
                  className={({ isActive }) =>
                    `rounded px-3 py-2 text-sm ${isActive ? "bg-orange-500 text-white" : "bg-orange-100 text-orange-900 hover:bg-orange-200"}`
                  }
                >
                  👥 Usuarios
                </NavLink>
                <NavLink
                  to="/gastos"
                  className={({ isActive }) =>
                    `rounded px-3 py-2 text-sm ${isActive ? "bg-orange-500 text-white" : "bg-orange-100 text-orange-900 hover:bg-orange-200"}`
                  }
                >
                  📊 Gastos
                </NavLink>
              </>
            )}

            {isStock && (
              <>
                <NavLink
                  to="/stock"
                  className={({ isActive }) =>
                    `rounded px-3 py-2 text-sm ${isActive ? "bg-orange-500 text-white" : "bg-orange-100 text-orange-900 hover:bg-orange-200"}`
                  }
                >
                  📦 Stock
                </NavLink>
                <NavLink
                  to="/ingredientes"
                  className={({ isActive }) =>
                    `rounded px-3 py-2 text-sm ${isActive ? "bg-orange-500 text-white" : "bg-orange-100 text-orange-900 hover:bg-orange-200"}`
                  }
                >
                  🧂 Ingredientes
                </NavLink>
              </>
            )}

            {isPedidos && (
              <>
                <NavLink
                  to="/ventas"
                  className={({ isActive }) =>
                    `rounded px-3 py-2 text-sm ${isActive ? "bg-orange-500 text-white" : "bg-orange-100 text-orange-900 hover:bg-orange-200"}`
                  }
                >
                  💰 Ventas
                </NavLink>
                <NavLink
                  to="/operaciones-pedidos"
                  className={({ isActive }) =>
                    `rounded px-3 py-2 text-sm ${isActive ? "bg-orange-500 text-white" : "bg-orange-100 text-orange-900 hover:bg-orange-200"}`
                  }
                >
                  🍳 Pedidos en vivo
                </NavLink>
              </>
            )}
            {isAdmin && (
              <NavLink
                to="/operaciones-pedidos"
                className={({ isActive }) =>
                  `rounded px-3 py-2 text-sm ${isActive ? "bg-orange-500 text-white" : "bg-orange-100 text-orange-900 hover:bg-orange-200"}`
                }
              >
                🍳 Pedidos en vivo
              </NavLink>
            )}
          </nav>
        )}
      </div>
    </header>
  );
}
