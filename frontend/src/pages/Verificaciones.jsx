import React, { useEffect, useState } from "react"; 
import Swal from "sweetalert2";
import "./Unidades.css";
import { API_URL } from "../config";
import ModalFile from "../components/ModalFile";
import Select from "react-select"; // Asegúrate de tener react-select instalado


// Meses por engomado
const MESES_ENGOMADO = {
  primer_semestre: { amarillo: [1, 2], rosa: [2, 3], rojo: [3, 4], verde: [4, 5], azul: [5, 6] },
  segundo_semestre: { amarillo: [7, 8], rosa: [8, 9], rojo: [9, 10], verde: [10, 11], azul: [11, 12] }
};

const ultimoDiaMes = (año, mes) => new Date(año, mes, 0).getDate();

const calcularFechaPorEngomado = (periodo, engomado, año) => {
  if (!engomado) return "";
  let meses = [];
  if (periodo === "1") meses = MESES_ENGOMADO.primer_semestre[engomado.toLowerCase()] || [];
  else if (periodo === "2") meses = MESES_ENGOMADO.segundo_semestre[engomado.toLowerCase()] || [];
  if (meses.length === 0) return "";
  const ultimoMes = Math.max(...meses);
  const ultimoDia = ultimoDiaMes(año, ultimoMes);
  return new Date(año, ultimoMes - 1, ultimoDia).toISOString().split("T")[0];
};

const calcularInicioPeriodo = (fechaSugerida) => {
  if (!fechaSugerida) return null;
  const fecha = new Date(fechaSugerida);
  fecha.setMonth(fecha.getMonth() - 2); // restar 2 meses
  return fecha;
};

const Verificaciones = () => {
  const [verificaciones, setVerificaciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [idUnidad, setIdUnidad] = useState("");
  const [periodoSeleccionado, setPeriodoSeleccionado] = useState("1");
  const [periodoReal, setPeriodoReal] = useState("");
  const [fechaSugerida, setFechaSugerida] = useState("");
  const [holograma, setHolograma] = useState("");
  const [folio, setFolio] = useState("");
  const [engomado, setEngomado] = useState("");
  const [placa, setPlaca] = useState("");
  const [archivo, setArchivo] = useState(null);

  const añoActual = new Date().getFullYear();
  const ultimos3Años = [añoActual, añoActual - 1, añoActual - 2];
  const [usarAñoAnterior, setUsarAñoAnterior] = useState(false);
  const [añoSeleccionado, setAñoSeleccionado] = useState(añoActual);

  const [unidadExiste, setUnidadExiste] = useState(false);
  const [verificacionExistente, setVerificacionExistente] = useState(null);
  const [checkingUnidad, setCheckingUnidad] = useState(false);
  const [formDisabled, setFormDisabled] = useState(false);
  const [modalUrl, setModalUrl] = useState(null);
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [unidades, setUnidades] = useState([]); // lista de todas las unidades

  // ------------------------------------------------------------------
  // Función para obtener todas las verificaciones
  // ------------------------------------------------------------------
  const obtenerVerificaciones = async () => {
    try {
      const res = await fetch(`${API_URL}/api/verificaciones`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const dataWithEstado = data.map((v) => {
        let estado = "PENDIENTE";
        if (v.proxima_verificacion) {
          const fechaProx = new Date(v.proxima_verificacion);
          const hoy = new Date();
          estado = hoy > fechaProx ? "ATRASADA" : "EN TIEMPO";
        }
        return { ...v, estado_verificacion: estado, fecha_limite: v.proxima_verificacion || null };
      });

      setVerificaciones(Array.isArray(dataWithEstado) ? dataWithEstado : []);
    } catch (err) {
      console.error("Error al obtener verificaciones:", err);
      Swal.fire({ icon: "error", title: "Error", text: "No se pudieron cargar las verificaciones." });
    } finally {
      setLoading(false);
    }
  };

    useEffect(() => {
    const obtenerUnidades = async () => {
      try {
        const res = await fetch(`${API_URL}/api/unidades`);
        if (!res.ok) throw new Error("Error al cargar unidades");
        const data = await res.json();
        setUnidades(data);
      } catch (err) {
        console.error(err);
        Swal.fire({ icon: "error", title: "Error", text: "No se pudieron cargar las unidades." });
      }
    };

    obtenerUnidades();
  }, []);

const eliminarVerificacion = async (id_verificacion) => {
  const confirm = await Swal.fire({
    title: "¿Estás seguro?",
    text: "Esta acción eliminará la verificación permanentemente.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#d33",
    cancelButtonColor: "#3085d6",
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar"
  });

  if (confirm.isConfirmed) {
    try {
      const res = await fetch(`${API_URL}/api/verificaciones/${id_verificacion}`, {
        method: "DELETE"
      });
      const data = await res.json();
      if (res.ok) {
        Swal.fire({ icon: "success", title: "Eliminado", text: data.message || "Verificación eliminada." });
        obtenerVerificaciones(); // recarga la tabla
      } else {
        Swal.fire({ icon: "error", title: "Error", text: data.error || "No se pudo eliminar." });
      }
    } catch (err) {
      console.error(err);
      Swal.fire({ icon: "error", title: "Error", text: "Ocurrió un error al eliminar." });
    }
  }
};


  // ------------------------------------------------------------------
  // Función para comprobar unidad y mostrar formulario solo si procede
  // ------------------------------------------------------------------
const checkUnidadLocal = async () => {
  if (!idUnidad) {
    setUnidadExiste(false);
    setVerificacionExistente(null);
    setEngomado("");
    setPlaca("");
    setFechaSugerida("");
    setFormDisabled(false);
    setMostrarFormulario(false);
    return;
  }

  setCheckingUnidad(true);

  try {
    const res = await fetch(`${API_URL}/api/unidad/${idUnidad}`);
    if (!res.ok) throw new Error("Unidad no encontrada");
    const data = await res.json();

    setPlaca(data.placa || "");
    setEngomado(data.engomado || "");

    const añoRegistro = usarAñoAnterior ? añoSeleccionado : añoActual;

    // Buscar verificación existente del año seleccionado
    const found = verificaciones.find(v =>
      String(v.id_unidad) === String(idUnidad) &&
      ((v.periodo_1 && new Date(v.periodo_1).getFullYear() === añoRegistro) ||
       (v.periodo_2 && new Date(v.periodo_2).getFullYear() === añoRegistro))
    );

    // Bloqueo por holograma 00 vigente
    const holograma00 = verificaciones.find(v =>
      String(v.id_unidad) === String(idUnidad) &&
      v.holograma === "00" &&
      v.proxima_verificacion &&
      new Date(v.proxima_verificacion) > new Date()
    );

    if (holograma00) {
      setUnidadExiste(true);
      setVerificacionExistente(holograma00);
      setHolograma("00");
      setFormDisabled(true);
      setPeriodoSeleccionado("1");
      setFechaSugerida(new Date(holograma00.proxima_verificacion).toISOString().split("T")[0]);
      setMostrarFormulario(true);

      Swal.fire({
        icon: "info",
        title: "Holograma 00 vigente",
        text: `No se puede registrar un nuevo periodo. Holograma 00 vigente hasta ${new Date(holograma00.proxima_verificacion).toLocaleDateString()}.`,
        timer: 4000,
        showConfirmButton: false
      });
      return;
    }

  // NUEVA VALIDACIÓN: si no tiene placa
  if (!data.placa) {
    setUnidadExiste(true);
    setFormDisabled(true);
    setMostrarFormulario(true);
    Swal.fire({
      icon: "warning",
      title: "Sin placa",
      text: "Esta unidad no tiene placa registrada. No se puede registrar la verificación.",
      timer: 4000,
      showConfirmButton: false
    });
    return; // salir de la función
  }
    if (!found) {
      setUnidadExiste(false);
      setVerificacionExistente(null);
      setFormDisabled(false);
      setFechaSugerida("");
      setMostrarFormulario(true);
      Swal.fire({
        icon: "info",
        title: "Automóvil sin registro",
        text: `Puedes ingresar un nuevo periodo para el año ${añoRegistro}.`,
        timer: 3000,
        showConfirmButton: false
      });
      return;
    }

    // Si hay proxima verificacion futura, bloquear
    if (found.proxima_verificacion && new Date(found.proxima_verificacion) > new Date()) {
      setUnidadExiste(true);
      setVerificacionExistente(found);
      setFormDisabled(true);
      setPeriodoSeleccionado("1");
      setFechaSugerida(new Date(found.proxima_verificacion).toISOString().split("T")[0]);
      setMostrarFormulario(true);

      Swal.fire({
        icon: "info",
        title: "Registro bloqueado",
        text: `No puedes registrar un nuevo periodo. Próxima verificación programada para ${new Date(found.proxima_verificacion).toLocaleDateString()}.`,
        timer: 4000,
        showConfirmButton: false
      });
      return;
    }

    // Si solo existe periodo_2 sin periodo_1, bloquear
    if (!found.periodo_1 && found.periodo_2) {
      setUnidadExiste(true);
      setVerificacionExistente(found);
      setPeriodoSeleccionado("1");
      setFormDisabled(true);
      setMostrarFormulario(true);

      Swal.fire({
        icon: "warning",
        title: "Periodo 2 existente",
        text: "No se puede registrar el periodo 1 después de que el periodo 2 ya está registrado.",
        timer: 4000,
        showConfirmButton: false
      });
      return;
    }

    // Unidad con verificación del año seleccionado
    setUnidadExiste(true);
    setVerificacionExistente(found);
    setHolograma(found.holograma || "");
    setFolio(found.folio_verificacion || "");

    let bloquear = false;

    if (found.periodo_1 && found.periodo_2) {
      bloquear = true;
      setFormDisabled(true);
      const vigencia = found.proxima_verificacion ? new Date(found.proxima_verificacion) : null;
      Swal.fire({
        icon: "info",
        title: "Periodos completos",
        text: `Esta unidad ya tiene ambos periodos registrados para el año ${añoRegistro}.${vigencia ? ` Vigencia hasta: ${vigencia.toLocaleDateString()}` : ""}`,
        timer: 4000,
        showConfirmButton: false
      });
    } else if (found.periodo_1 && !found.periodo_2) {
      setPeriodoSeleccionado("2");
      Swal.fire({
        icon: "info",
        title: "Aviso",
        text: "El periodo 1 ya está registrado. Se seleccionó automáticamente el periodo 2.",
        timer: 2500,
        showConfirmButton: false
      });
    } else {
      setPeriodoSeleccionado("1");
    }

    setFormDisabled(bloquear);
    setMostrarFormulario(true);

  } catch (err) {
    console.error(err);
    Swal.fire({ icon: "error", title: "Error", text: "No se encontró la unidad." });
    setEngomado("");
    setPlaca("");
    setUnidadExiste(false);
    setVerificacionExistente(null);
    setFechaSugerida("");
    setFormDisabled(false);
    setMostrarFormulario(false);
  } finally {
    setCheckingUnidad(false);
  }
};

  const handleIdBlur = () => checkUnidadLocal();
  const handleFileChange = (e) => setArchivo(e.target.files[0] ?? null);

  const resetForm = () => {
    setIdUnidad("");
    setPeriodoSeleccionado("1");
    setPeriodoReal("");
    setFechaSugerida("");
    setHolograma("");
    setFolio("");
    setEngomado("");
    setPlaca("");
    setArchivo(null);
    setUnidadExiste(false);
    setVerificacionExistente(null);
    setFormDisabled(false);
    setUsarAñoAnterior(false);
    setAñoSeleccionado(añoActual);
    setMostrarFormulario(false);
  };

  // Actualiza fecha sugerida y real editable
  useEffect(() => {
    const año = usarAñoAnterior ? añoSeleccionado : añoActual;
    if (verificacionExistente) {
      const fechaExistente = periodoSeleccionado === "1" ? verificacionExistente.periodo_1_real : verificacionExistente.periodo_2_real;
      const vigencia = verificacionExistente.proxima_verificacion ? new Date(verificacionExistente.proxima_verificacion) : null;
      setFechaSugerida(vigencia ? vigencia.toISOString().split("T")[0] : calcularFechaPorEngomado(periodoSeleccionado, engomado, año));
      setPeriodoReal(fechaExistente || (vigencia ? vigencia.toISOString().split("T")[0] : calcularFechaPorEngomado(periodoSeleccionado, engomado, año)));
    } else {
      setFechaSugerida(calcularFechaPorEngomado(periodoSeleccionado, engomado, año));
      setPeriodoReal(calcularFechaPorEngomado(periodoSeleccionado, engomado, año));
    }
  }, [periodoSeleccionado, engomado, verificacionExistente, usarAñoAnterior, añoSeleccionado]);

  // Submit
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formDisabled) return;

    if (!idUnidad) return Swal.fire({ icon: "warning", title: "ID requerido", text: "Indica el ID de la unidad." });
    if (!archivo) return Swal.fire({ icon: "warning", title: "Archivo requerido", text: "Debes seleccionar un PDF." });

    if (fechaSugerida && new Date(periodoReal) > new Date(fechaSugerida)) {
      return Swal.fire({ icon: "warning", title: "Fecha inválida", text: "La fecha real no puede superar la fecha límite." });
    }

    const formData = new FormData();
    formData.append("id_unidad", idUnidad);
    formData.append(`periodo_${periodoSeleccionado}`, fechaSugerida);
    formData.append(`periodo_${periodoSeleccionado}_real`, periodoReal);
    if (holograma) formData.append("holograma", holograma);
    if (folio) formData.append("folio_verificacion", folio);
    if (engomado) formData.append("engomado", engomado);
    formData.append("archivo", archivo);

    try {
      const res = await fetch(`${API_URL}/api/verificaciones`, { method: "POST", body: formData });
      const data = await res.json();

      if (res.ok) {
        Swal.fire({ icon: "success", title: "Éxito", text: data.message || "Operación completada." });
        resetForm();
        obtenerVerificaciones();
      } else {
        Swal.fire({ icon: "error", title: "Error", text: data.error || "Fallo en el servidor." });
      }
    } catch (err) {
      console.error("Error al enviar verificación:", err);
      Swal.fire({ icon: "error", title: "Error", text: "Ocurrió un error al enviar la verificación." });
    }
  };

  useEffect(() => { obtenerVerificaciones(); }, []);

  if (loading) return <p className="text-center mt-5 fw-bold">Cargando verificaciones...</p>;

  return (
    <div className="unidades-container">
      <h1><i className="fa-solid fa-car-side"></i> Verificaciones</h1>
        <form onSubmit={handleSubmit} className="d-flex flex-column gap-2">
          <div className="d-flex gap-2 mb-3" style={{ alignItems: "flex-end" }}>
            <div style={{ width: "300px" }}> {/* aquí defines el ancho deseado */}
              <label style={{ fontSize: "0.9rem" }}>Unidad:</label>
              <Select
                options={unidades.map(u => ({
                  value: u.id_unidad,
                  label: `${u.id_unidad} - ${u.marca} ${u.vehiculo} ${u.modelo}`
                }))}
                value={
                  idUnidad
                    ? {
                        value: idUnidad,
                        label: (() => {
                          const selected = unidades.find(u => u.id_unidad === idUnidad);
                          return selected
                            ? `${selected.id_unidad} - ${selected.marca} ${selected.vehiculo} ${selected.modelo}`
                            : idUnidad;
                        })(),
                      }
                    : null
                }
                onChange={(opt) => setIdUnidad(opt ? opt.value : "")}
                isClearable
                isSearchable
                placeholder="Busca o selecciona unidad"
                styles={{
                  container: (base) => ({ ...base, width: "100%" }), // ocupa todo el ancho del div padre
                  control: (base) => ({ ...base, minHeight: 35 }),
                  menu: (base) => ({ ...base, zIndex: 9999 }),
                }}
              />
            </div>

            <button
              type="button"
              className="btn btn-outline-danger"
              onClick={checkUnidadLocal}
              disabled={checkingUnidad}
              style={{ height: 35 }}
            >
              Comprobar unidad
            </button>
          </div>
          {formDisabled && (
            <div className="alert alert-info py-1">
              Esta unidad no puede registrar otro periodo todavía.
            </div>
            )}
          {/* Mostrar placa y engomado solo después de verificar unidad */}
          {mostrarFormulario && !formDisabled && (
            <>
              <h5 className="fw-bold mb-3 text-center">Registrar / Actualizar Verificación</h5>
              <input type="text" placeholder="Placa" value={placa} readOnly className="form-control" />
              <input type="text" placeholder="Engomado" value={engomado} readOnly className="form-control" />
            </>
          )}
          {/* Mostrar formulario solo después de verificar unidad */}
          {mostrarFormulario && !formDisabled && (
            <>
              <div className="d-flex gap-2 align-items-center">
                <select className="form-select" value={periodoSeleccionado} onChange={(e) => setPeriodoSeleccionado(e.target.value)}>
                  <option value="1" disabled={verificacionExistente?.periodo_1}>Periodo 1</option>
                  <option value="2" disabled={verificacionExistente?.periodo_2 || (verificacionExistente?.holograma === "00" && new Date() < new Date(fechaSugerida))}>
                    Periodo 2
                  </option>
                </select>

                <label className="mb-0">Año anterior</label>
                <input type="checkbox" checked={usarAñoAnterior} onChange={(e) => setUsarAñoAnterior(e.target.checked)} />
                {usarAñoAnterior && (
                  <select className="form-select" value={añoSeleccionado} onChange={(e) => setAñoSeleccionado(parseInt(e.target.value))}>
                    {ultimos3Años.map(año => <option key={año} value={año}>{año}</option>)}
                  </select>
                )}
              </div>

              <div className="d-flex gap-2 align-items-center">
                <label className="mb-0">Fecha límite sugerida</label>
                <input type="date" value={fechaSugerida} readOnly className="form-control" />

                <label className="mb-0">Fecha real registrada</label>
                <input type="date" value={periodoReal} onChange={(e) => setPeriodoReal(e.target.value)} className="form-control" />
              </div>

              <input type="text" placeholder="Holograma" value={holograma} onChange={(e) => setHolograma(e.target.value)} />
              <input type="text" placeholder="Folio" value={folio} onChange={(e) => setFolio(e.target.value)} />
              <input type="file" accept="application/pdf" onChange={handleFileChange} required />

              <div className="d-flex gap-2">
                <button type="submit" className="btn btn-danger fw-bold" disabled={formDisabled}>📄 Registrar Verificación</button>
                <button type="button" className="btn btn-outline-secondary" onClick={resetForm}>Limpiar</button>
              </div>
            </>
          )}
        </form>


      {/* Tabla de verificaciones */}
      <div className="table-responsive shadow rounded">
        <table className="elegant-table">
          <thead className="table-dark text-center">
            <tr>
              <th className="ocultar">ID</th><th>ID</th><th>Unidad</th><th>Placa</th><th>Modelo</th><th>Última</th>
              <th className="ocultar">Periodo 1</th><th>1 periodo realizado</th><th>Talon 1 verif.</th>
              <th className="ocultar">Periodo 2</th><th>2 periodo realizado</th><th>Talon 2 verif.</th>
              <th>Holograma</th><th>Folio</th><th>Engomado</th>
              <th>Estado</th><th>Próxima Verificación</th><th>Acciones</th>

            </tr>
          </thead>
          <tbody className="text-center">
            {verificaciones.length > 0 ? verificaciones.map((v) => (
              <tr key={v.id_verificacion} className={
                v.estado_verificacion === "EN TIEMPO" ? "table-success" :
                v.estado_verificacion === "ATRASADA" ? "table-danger" :
                v.estado_verificacion === "PENDIENTE" ? "table-warning" : ""
              } >
                <td className="ocultar">{v.id_verificacion}</td>
                <td>{v.id_unidad}</td>
                <td>{v.marca} {v.vehiculo}</td>
                <td>{v.placa}</td>
                <td>{v.modelo}</td>
                <td>{v.ultima_verificacion}</td>
                <td className="ocultar" >{v.periodo_1}</td>
                <td>{v.periodo_1_real}</td>
                <td>
                  {v.url_verificacion_1 ? (
                    <button
                      className="btn btn-outline-danger btn-sm"
                      onClick={() => setModalUrl(`${API_URL}/${v.url_verificacion_1}`)}
                    >
                      Ver PDF
                    </button>
                  ) : ""}
                </td>
                <td className="ocultar">{v.periodo_2}</td>
                <td>{v.periodo_2_real}</td>
                <td>
                  {v.url_verificacion_2 ? (
                    <button
                      className="btn btn-outline-danger btn-sm"
                      onClick={() => setModalUrl(`${API_URL}/${v.url_verificacion_2}`)}
                    >
                      Ver PDF
                    </button>
                  ) : ""}
                </td>
                <td>{v.holograma}</td>
                <td>{v.folio_verificacion}</td>
                <td>{v.engomado}</td>
                <td>{v.estado_verificacion}</td>
                <td>{v.proxima_verificacion}</td>
                <td>
                  <button
                    className="btn btn-outline-danger btn-sm"
                    onClick={() => eliminarVerificacion(v.id_verificacion)}
                  >
                    Eliminar
                  </button>
                </td>

              </tr>
            )) : <tr><td colSpan="17">No hay verificaciones registradas</td></tr>}
          </tbody>
        </table>
      </div>

      {modalUrl && <ModalFile url={modalUrl} onClose={() => setModalUrl(null)} />}
    </div>
  );
};

export default Verificaciones;
