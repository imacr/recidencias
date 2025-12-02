import { useEffect, useState } from "react"; 
import Swal from "sweetalert2";
import { API_URL } from "../config";

export default function Mantenimientos({ registroPrellenado }) {
  const [tipos, setTipos] = useState([]);
  const [form, setForm] = useState({
    id_unidad: "",
    tipo_mantenimiento: "",
    descripcion: "",
    fecha_realizacion: "",
    kilometraje: "",
    realizado_por: "",
    empresa_garantia: "",
    cobertura_garantia: "",
    costo: "",
    observaciones: "",
    url_comprobante: null,
  });

  useEffect(() => {
    fetch(`${API_URL}/tipos_mantenimiento`)
      .then((res) => res.json())
      .then(setTipos)
      .catch((err) => console.error("Error cargando tipos:", err));
  }, []);

  useEffect(() => {
    if (registroPrellenado) {
      setForm((prev) => ({
        ...prev,
        id_unidad: registroPrellenado.id_unidad,
        tipo_mantenimiento: registroPrellenado.tipo,
        kilometraje: registroPrellenado.kilometraje_actual || "",
      }));
    }
  }, [registroPrellenado]);

  const handleChange = (e) => {
    const { name, value, files } = e.target;
    if (files) {
      setForm((prev) => ({ ...prev, [name]: files[0] }));
    } else {
      setForm((prev) => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.tipo_mantenimiento || !form.id_unidad || !form.fecha_realizacion) {
      Swal.fire("Campos incompletos", "Llena los obligatorios", "warning");
      return;
    }

    const formData = new FormData();
    Object.keys(form).forEach((key) => {
      if (form[key] !== null && form[key] !== undefined) {
        formData.append(key, form[key]);
      }
    });

    try {
      const res = await fetch(`${API_URL}/mantenimientos`, {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        Swal.fire("Éxito", "Mantenimiento registrado correctamente", "success");
        setForm({
          id_unidad: "",
          tipo_mantenimiento: "",
          descripcion: "",
          fecha_realizacion: "",
          kilometraje: "",
          realizado_por: "",
          empresa_garantia: "",
          cobertura_garantia: "",
          costo: "",
          observaciones: "",
          url_comprobante: null,
        });
      } else {
        const errData = await res.json();
        Swal.fire("Error", errData.error || "No se pudo registrar", "error");
      }
    } catch (error) {
      console.error(error);
      Swal.fire("Error", "Error de conexión con el servidor", "error");
    }
  };

  return (
    <div className="container mt-4">
      <h2 className="text-center mb-4">Registro de Mantenimientos</h2>
      <form onSubmit={handleSubmit} className="p-4 shadow rounded bg-light">

        {/* Fila 1 */}
        <div className="row">
          <div className="col-md-4 mb-3">
            <label>Unidad (ID)</label>
            <input
              type="number"
              name="id_unidad"
              value={form.id_unidad}
              onChange={handleChange}
              placeholder="Ej: 101"
              className="form-control"
              required
            />
          </div>
          <div className="col-md-4 mb-3">
            <label>Tipo de Mantenimiento</label>
            <select
              name="tipo_mantenimiento"
              value={form.tipo_mantenimiento}
              onChange={handleChange}
              className="form-select"
              required
            >
              <option value="">Ej: Preventivo</option>
              {tipos.map((t) => (
                <option key={t.id_tipo_mantenimiento} value={t.nombre_tipo}>
                  {t.nombre_tipo}
                </option>
              ))}
            </select>
          </div>
          <div className="col-md-4 mb-3">
            <label>Fecha Realización</label>
            <input
              type="date"
              name="fecha_realizacion"
              value={form.fecha_realizacion}
              onChange={handleChange}
              placeholder="Ej: 2025-11-27"
              className="form-control"
              required
            />
          </div>
        </div>

        {/* Fila 2 */}
        <div className="row">
          <div className="col-md-4 mb-3">
            <label>Kilometraje</label>
            <input
              type="number"
              name="kilometraje"
              value={form.kilometraje}
              placeholder="Ej: 15000 km"
              className="form-control"
              readOnly
            />
          </div>
          <div className="col-md-4 mb-3">
            <label>Realizado por</label>
            <input
              type="text"
              name="realizado_por"
              value={form.realizado_por}
              onChange={handleChange}
              placeholder="Ej: Juan Pérez"
              className="form-control"
            />
          </div>
          <div className="col-md-4 mb-3">
            <label>Costo (MXN)</label>
            <input
              type="number"
              step="0.01"
              name="costo"
              value={form.costo}
              onChange={handleChange}
              placeholder="Ej: 2500.50"
              className="form-control"
            />
          </div>
        </div>

        {/* Fila 3 */}
        <div className="row">
          <div className="col-md-6 mb-3">
            <label>Empresa Garantía</label>
            <input
              type="text"
              name="empresa_garantia"
              value={form.empresa_garantia}
              onChange={handleChange}
              placeholder="Ej: Garantías XYZ S.A."
              className="form-control"
            />
          </div>
          <div className="col-md-6 mb-3">
            <label>Cobertura Garantía</label>
            <input
              type="text"
              name="cobertura_garantia"
              value={form.cobertura_garantia}
              onChange={handleChange}
              placeholder="Ej: Motor y transmisión por 1 año"
              className="form-control"
            />
          </div>
        </div>

        {/* Textareas */}
        <div className="mb-3">
          <label>Descripción</label>
          <textarea
            name="descripcion"
            value={form.descripcion}
            onChange={handleChange}
            placeholder="Ej: Cambio de aceite y filtro, revisión de frenos"
            className="form-control"
            rows="3"
          />
        </div>

        <div className="mb-3">
          <label>Observaciones</label>
          <textarea
            name="observaciones"
            value={form.observaciones}
            onChange={handleChange}
            placeholder="Ej: Unidad entregada sin problemas, cliente satisfecho"
            className="form-control"
            rows="2"
          />
        </div>

        {/* Archivo */}
        <div className="mb-3">
          <label>Comprobante (Imagen o PDF)</label>
          <input
            type="file"
            name="url_comprobante"
            accept="image/*,application/pdf"
            onChange={handleChange}
            className="form-control"
          />
        </div>

        {/* Botón */}
        <div className="text-center">
          <button type="submit" className="btn btn-success">
            Registrar Mantenimiento
          </button>
        </div>
      </form>
    </div>
  );
}
