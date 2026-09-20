"""Modelos de activos y física simplificada para Sitio 3."""

import random

class Reefer:
    def __init__(self, sid, rng, setpoint=-18.0):
        self.sid = sid
        self.rng = rng
        self.setpoint = setpoint
        self.temp = setpoint + rng.uniform(-0.4, 0.4)
        self.puerta_abierta = False

    def tick(self, dt_s):
        if self.puerta_abierta:
            self.temp += 0.9 * (dt_s / 60.0)
        else:
            self.temp += (self.setpoint - self.temp) * 0.08
        self.temp += self.rng.gauss(0.0, 0.05)
        return round(self.temp, 2)

class SensorFisico:
    """Modelo genérico con inercia, ruido y límites opcionales."""

    def __init__(
        self,
        sid,
        metric,
        unit,
        rng,
        base,
        noise,
        drift=0.0,
        min_value=None,
        max_value=None,
    ):
        self.sid = sid
        self.metric = metric
        self.unit = unit
        self.rng = rng
        self.value = base
        self.noise = noise
        self.drift = drift
        self.min_value = min_value
        self.max_value = max_value

    def tick(self, load=1.0):
        target = self.value + self.drift * load
        self.value += (target - self.value) * 0.05
        self.value += self.rng.gauss(0.0, self.noise)

        if self.min_value is not None:
            self.value = max(self.min_value, self.value)

        if self.max_value is not None:
            self.value = min(self.max_value, self.value)

        return round(self.value, 2)

class SimuladorSitio3:
    """Conjunto reproducible de puntos de medición del sitio."""

    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.reefer = [
            Reefer(f"REEFER_S3_{i:02d}", random.Random(seed + i))
            for i in range(1, 49)
        ]
        self.fajas = []
        for i in range(1, 7):
            self.fajas.append(SensorFisico(f"FAJA_S3_C{i}", "vibration", "mm/s",
                                           random.Random(seed+100+i), 2.0, 0.08))
            self.fajas.append(SensorFisico(f"FAJA_S3_C{i}", "current", "A",
                                           random.Random(seed+200+i), 35.0, 0.4))
        self.gruas = [
            SensorFisico("GRUA_S3_STS01", "current", "A", random.Random(seed+301), 120.0, 1.0),
            SensorFisico("GRUA_S3_STS02", "current", "A", random.Random(seed+302), 120.0, 1.0),
        ]
        self.ambientales = []
        for i in range(1, 13):
            self.ambientales.append(
                SensorFisico(
                    f"AMBIENTE_S3_{i:02d}",
                    "humidity",
                    "%",
                    random.Random(seed + 400 + i),
                    65.0,       # humedad inicial: 65 %
                    0.8,        # ruido
                    min_value=0.0,
                    max_value=100.0,
                )
            )

    def tick(self, dt_s=15):
        eventos = []
        for r in self.reefer:
            eventos.append((r.sid, "temperature", r.tick(dt_s), "C"))
        for s in self.fajas:
            eventos.append((s.sid, s.metric, s.tick(), s.unit))
        for s in self.gruas:
            eventos.append((s.sid, s.metric, s.tick(), s.unit))
        for s in self.ambientales:
            eventos.append((s.sid, s.metric, s.tick(), s.unit))
        return eventos

def generar_evento(rng, worker_id, sensor_id, metric, value, unit, timestamp, seq):
    from .esquema import construir_evento
    return construir_evento(timestamp, sensor_id, metric, value, unit, worker_id, seq)
