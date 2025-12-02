import { useEffect, useState } from "react";
import Swal from "sweetalert2";
import { API_URL } from "../config";
import Mantenimientos from "./Mantenimientos";
import "./Unidades.css";

export default function MantenimientosMenores() {
  const [programados, setProgramados] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [registroSeleccionado, setRegistroSeleccionado] = useState(null);

  // Filtros
  const [filtroID, setFiltroID] = useState("");
  const [filtroMarca, setFiltroMarca] = useState("");
  const [filtroClase, setFiltroClase] = useState("");

  // Paginación
  const [paginaActual, setPaginaActual] = useState(1);
  const [itemsPorPagina, setItemsPorPagina] = useState(5);

  const fetchProgramados = async () => {
    try {
      const res = await fetch(`${API_URL}/mantenimientos_programados`);
      if (!res.ok) throw new Error("Error al obtener los mantenimientos");
      const data = await res.json();
      setProgramados(data.filter(p => p.tipo.toLowerCase() === "menor"));
      setError(false);
    } catch (err) {
      console.error(err);
      setError(true);
      Swal.fire("Error", "No se pudieron cargar los mantenimientos menores", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProgramados();
  }, []);

  const handleRegistrar = (p) => {
    Swal.fire({
      title: "Registrar mantenimiento",
      text: `¿Deseas registrar el mantenimiento menor para la unidad ${p.id_unidad} - ${p.marca} ${p.clase_tipo}?`,
      icon: "question",
      showCancelButton: true,
      confirmButtonText: "Sí",
      cancelButtonText: "Cancelar",
    }).then((result) => {
      if (result.isConfirmed) setRegistroSeleccionado(p);
    });
  };

  const diasRestantes = (fecha) => {
    if (!fecha) return null;
    const hoy = new Date();
    const proxima = new Date(fecha);
    return Math.ceil((proxima - hoy) / (1000 * 60 * 60 * 24));
  };

  const filtrados = programados.filter(p => {
    return (
      (filtroID === "" || p.id_unidad.toString().includes(filtroID)) &&
      (filtroMarca === "" || p.marca.toLowerCase().includes(filtroMarca.toLowerCase())) &&
      (filtroClase === "" || p.clase_tipo.toLowerCase().includes(filtroClase.toLowerCase()))
    );
  });

  const totalPaginas = itemsPorPagina === "all" ? 1 : Math.ceil(filtrados.length / itemsPorPagina);
  const mostrarFilas = itemsPorPagina === "all"
    ? filtrados
    : filtrados.slice((paginaActual - 1) * itemsPorPagina, paginaActual * itemsPorPagina);

  return (
    <div className="unidades-container">
      <h1>Mantenimientos Menores</h1>

      {/* Filtros */}
      <div className="filtros">
        <input type="text" placeholder="Filtrar por ID" value={filtroID} onChange={(e) => setFiltroID(e.target.value)} />
        <input type="text" placeholder="Filtrar por Marca" value={filtroMarca} onChange={(e) => setFiltroMarca(e.target.value)} />
        <input type="text" placeholder="Filtrar por Clase" value={filtroClase} onChange={(e) => setFiltroClase(e.target.value)} />
      </div>

      {/* Selección de items por página */}
      <div className="paginacion-control">
        <label>Mostrar: </label>
        <select value={itemsPorPagina} onChange={(e) => { setItemsPorPagina(e.target.value === "all" ? "all" : parseInt(e.target.value)); setPaginaActual(1); }}>
          <option value={5}>5</option>
          <option value={10}>10</option>
          <option value={20}>20</option>
          <option value="all">Todos</option>
        </select>
      </div>

      {loading ? (
        <div className="mensaje-estado">Cargando datos...</div>
      ) : error ? (
        <div className="mensaje-estado error">Error al cargar los datos.</div>
      ) : (
        <div className="table-wrapper">
          <table className="elegant-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Marca</th>
                <th>Clase tipo</th>
                <th>Tipo</th>
                <th>Último Mantenimiento</th>
                <th>Kilometraje Último</th>
                <th>Próximo Mantenimiento</th>
                <th>Próximo Kilometraje</th>
                <th>Días Restantes</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>
              {mostrarFilas.length > 0 ? (
                mostrarFilas.map((p) => {
                  const dias = diasRestantes(p.proximo_mantenimiento);
                  const kmRestante = (p.proximo_kilometraje || 0) - (p.kilometraje_ultimo || 0);
                  const activar = dias !== null && kmRestante !== null && (dias <= 7 || kmRestante <= 500 || dias < 0 || kmRestante < 0);

                  const alerta =
                    dias < 0 || kmRestante < 0
                      ? "alerta-vencido-menor"
                      : dias <= 7 || kmRestante <= 500
                      ? "alerta-proximo-menor"
                      : "";

                  return (
                    <tr key={p.id_mantenimiento_programado} className={alerta}>
                      <td>{p.id_unidad}</td>
                      <td>{p.marca}</td>
                      <td>{p.clase_tipo}</td>
                      <td>{p.tipo}</td>
                      <td>{p.fecha_ultimo_mantenimiento || "-"}</td>
                      <td>{p.kilometraje_ultimo || "-"}</td>
                      <td>{p.proximo_mantenimiento || "-"}</td>
                      <td>{p.proximo_kilometraje || "-"}</td>
                      <td>{dias !== null ? (dias >= 0 ? `${dias} días` : "Vencido") : "-"}</td>
                      <td>
                        <button
                          className="btn-registrar"
                          disabled={!activar}
                          onClick={() => handleRegistrar(p)}
                        >
                          Registrar
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="10" style={{ textAlign: "center" }}>
                    No hay mantenimientos menores programados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          {/* Paginación */}
          {itemsPorPagina !== "all" && (
            <div className="paginacion">
              <button onClick={() => setPaginaActual((prev) => Math.max(prev - 1, 1))} disabled={paginaActual === 1}>
                {"<"}
              </button>
              <span>Página {paginaActual} de {totalPaginas}</span>
              <button onClick={() => setPaginaActual((prev) => Math.min(prev + 1, totalPaginas))} disabled={paginaActual === totalPaginas}>
                {">"}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Modal para el formulario */}
      {registroSeleccionado && (
        <div className="modal-overlay" onClick={() => setRegistroSeleccionado(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="btn btn-secondary mb-3" onClick={() => setRegistroSeleccionado(null)}>
              Cerrar
            </button>
            <Mantenimientos registroPrellenado={registroSeleccionado} />
          </div>
        </div>
      )}
    </div>
  );
}
