"""
athenahealth to IHEP Canonical Format Mapping

Transforms athenahealth API responses (athenaClinicals, athenaCoordinator)
into the IHEP canonical data format.

Author: Jason M Jarmacz | Co-Author: Claude by Anthropic
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class AthenaToIHEPMapper:
    """
    Maps athenahealth API data to IHEP canonical format.

    athenahealth uses both FHIR R4 endpoints and proprietary REST API
    responses. This mapper handles both, normalizing department IDs,
    provider mappings, and athena-specific data structures.
    """

    ATHENA_EXTENSION_BASE = "http://athenahealth.com/fhir/extension"

    def map_patient(self, athena_patient: Dict) -> Dict:
        """
        Map athenahealth patient to IHEP canonical format.

        Handles both FHIR R4 Patient and athena proprietary format
        (with fields like patientid, firstname, lastname, etc.).
        """
        ihep_patient = {
            "ihep_resource_type": "Patient",
            "source_vendor": "athenahealth",
            "source_id": (
                athena_patient.get("id")
                or str(athena_patient.get("patientid", ""))
            ),
            "active": athena_patient.get("active", True),
        }

        # Identifiers
        identifiers = []
        if "identifier" in athena_patient:
            for ident in athena_patient["identifier"]:
                identifiers.append({
                    "system": ident.get("system", ""),
                    "value": ident.get("value", ""),
                    "type": self._extract_identifier_type(ident),
                    "vendor_system": "athenahealth"
                })
        # Proprietary format
        if "patientid" in athena_patient:
            identifiers.append({
                "system": "urn:oid:2.16.840.1.113883.3.564",
                "value": str(athena_patient["patientid"]),
                "type": "MRN",
                "vendor_system": "athenahealth"
            })
        if "enterpriseid" in athena_patient:
            identifiers.append({
                "system": "athenahealth:enterpriseid",
                "value": str(athena_patient["enterpriseid"]),
                "type": "EID",
                "vendor_system": "athenahealth"
            })
        ihep_patient["identifiers"] = identifiers

        # Name
        names = []
        if "name" in athena_patient:
            for name in athena_patient["name"]:
                names.append({
                    "use": name.get("use", "official"),
                    "family": name.get("family", ""),
                    "given": name.get("given", []),
                    "prefix": name.get("prefix", []),
                    "suffix": name.get("suffix", []),
                })
        elif "firstname" in athena_patient or "lastname" in athena_patient:
            name_entry = {
                "use": "official",
                "family": athena_patient.get("lastname", ""),
                "given": [],
                "prefix": [],
                "suffix": [],
            }
            if athena_patient.get("firstname"):
                name_entry["given"].append(athena_patient["firstname"])
            if athena_patient.get("middlename"):
                name_entry["given"].append(athena_patient["middlename"])
            if athena_patient.get("suffix"):
                name_entry["suffix"].append(athena_patient["suffix"])
            names.append(name_entry)
        ihep_patient["name"] = names

        # Demographics
        ihep_patient["birth_date"] = (
            athena_patient.get("birthDate")
            or self._format_athena_date(athena_patient.get("dob", ""))
        )
        ihep_patient["gender"] = self._normalize_gender(
            athena_patient.get("gender")
            or athena_patient.get("sex", "")
        )

        # Address
        addresses = []
        if "address" in athena_patient:
            for addr in athena_patient["address"]:
                addresses.append({
                    "use": addr.get("use", "home"),
                    "line": addr.get("line", []),
                    "city": addr.get("city", ""),
                    "state": addr.get("state", ""),
                    "postal_code": addr.get("postalCode", ""),
                    "country": addr.get("country", "US"),
                })
        elif "address1" in athena_patient:
            lines = [athena_patient.get("address1", "")]
            if athena_patient.get("address2"):
                lines.append(athena_patient["address2"])
            addresses.append({
                "use": "home",
                "line": lines,
                "city": athena_patient.get("city", ""),
                "state": athena_patient.get("state", ""),
                "postal_code": athena_patient.get("zip", ""),
                "country": "US",
            })
        ihep_patient["address"] = addresses

        # Telecom
        telecoms = []
        if "telecom" in athena_patient:
            for t in athena_patient["telecom"]:
                telecoms.append({
                    "system": t.get("system", "phone"),
                    "value": t.get("value", ""),
                    "use": t.get("use", "home"),
                })
        else:
            for phone_field, use in [
                ("homephone", "home"),
                ("mobilephone", "mobile"),
                ("workphone", "work"),
            ]:
                if athena_patient.get(phone_field):
                    telecoms.append({
                        "system": "phone",
                        "value": athena_patient[phone_field],
                        "use": use,
                    })
            if athena_patient.get("email"):
                telecoms.append({
                    "system": "email",
                    "value": athena_patient["email"],
                    "use": "home",
                })
        ihep_patient["telecom"] = telecoms

        # athena-specific: department and provider
        if athena_patient.get("departmentid"):
            ihep_patient["managing_organization"] = {
                "reference": f"Organization/athena-dept-{athena_patient['departmentid']}",
                "display": athena_patient.get("departmentname", ""),
            }
        if athena_patient.get("primaryproviderid"):
            ihep_patient["primary_provider"] = {
                "reference": f"Practitioner/athena-prov-{athena_patient['primaryproviderid']}",
                "display": athena_patient.get("primaryprovidername", ""),
            }

        ihep_patient["extensions"] = self._extract_extensions(athena_patient)
        return ihep_patient

    def map_observation(self, athena_obs: Dict) -> Dict:
        """Map athenahealth observation/vital to IHEP canonical format."""
        ihep_obs = {
            "ihep_resource_type": "Observation",
            "source_vendor": "athenahealth",
            "source_id": athena_obs.get("id", ""),
            "status": athena_obs.get("status", "final"),
        }

        # Code
        code = athena_obs.get("code", {})
        ihep_obs["code"] = {
            "text": code.get("text", athena_obs.get("clinicalelementid", "")),
            "coding": [
                {
                    "system": c.get("system", ""),
                    "code": c.get("code", ""),
                    "display": c.get("display", ""),
                }
                for c in code.get("coding", [])
            ],
        }

        # Subject
        subject = athena_obs.get("subject", {})
        ihep_obs["subject"] = {
            "reference": subject.get("reference", ""),
            "display": subject.get("display", ""),
        }
        # Proprietary: link by patientid
        if not ihep_obs["subject"]["reference"] and athena_obs.get("patientid"):
            ihep_obs["subject"]["reference"] = (
                f"Patient/athena-{athena_obs['patientid']}"
            )

        # Value
        if "valueQuantity" in athena_obs:
            vq = athena_obs["valueQuantity"]
            ihep_obs["value"] = {
                "type": "Quantity",
                "value": vq.get("value"),
                "unit": vq.get("unit", ""),
                "system": vq.get("system", "http://unitsofmeasure.org"),
                "code": vq.get("code", ""),
            }
        elif "valueString" in athena_obs:
            ihep_obs["value"] = {
                "type": "String",
                "value": athena_obs["valueString"],
            }
        elif "value" in athena_obs:
            # Proprietary format
            ihep_obs["value"] = {
                "type": "String",
                "value": str(athena_obs["value"]),
            }
        else:
            ihep_obs["value"] = None

        ihep_obs["effective_date_time"] = (
            athena_obs.get("effectiveDateTime")
            or self._format_athena_date(athena_obs.get("readingdate", ""))
        )
        ihep_obs["issued"] = athena_obs.get("issued")

        # Category
        ihep_obs["category"] = []
        for cat in athena_obs.get("category", []):
            for coding in cat.get("coding", []):
                ihep_obs["category"].append({
                    "system": coding.get("system", ""),
                    "code": coding.get("code", ""),
                    "display": coding.get("display", ""),
                })

        ihep_obs["extensions"] = self._extract_extensions(athena_obs)
        return ihep_obs

    def map_appointment(self, athena_appt: Dict) -> Dict:
        """Map athenahealth appointment to IHEP canonical format."""
        ihep_appt = {
            "ihep_resource_type": "Appointment",
            "source_vendor": "athenahealth",
            "source_id": (
                athena_appt.get("id")
                or str(athena_appt.get("appointmentid", ""))
            ),
            "status": self._map_athena_appointment_status(
                athena_appt.get("status")
                or athena_appt.get("appointmentstatus", "")
            ),
            "start": (
                athena_appt.get("start")
                or self._format_athena_datetime(
                    athena_appt.get("date", ""),
                    athena_appt.get("starttime", "")
                )
            ),
            "end": athena_appt.get("end"),
            "minutes_duration": (
                athena_appt.get("minutesDuration")
                or athena_appt.get("duration")
            ),
            "description": (
                athena_appt.get("description", "")
                or athena_appt.get("appointmenttype", "")
            ),
        }

        # Participants
        participants = []
        if "participant" in athena_appt:
            for p in athena_appt["participant"]:
                actor = p.get("actor", {})
                participants.append({
                    "type": self._get_participant_type(p),
                    "actor": {
                        "reference": actor.get("reference", ""),
                        "display": actor.get("display", ""),
                    },
                    "status": p.get("status", "accepted"),
                })
        else:
            # Proprietary format
            if athena_appt.get("patientid"):
                participants.append({
                    "type": "patient",
                    "actor": {
                        "reference": f"Patient/athena-{athena_appt['patientid']}",
                        "display": athena_appt.get("patientname", ""),
                    },
                    "status": "accepted",
                })
            if athena_appt.get("providerid"):
                participants.append({
                    "type": "practitioner",
                    "actor": {
                        "reference": f"Practitioner/athena-{athena_appt['providerid']}",
                        "display": athena_appt.get("providername", ""),
                    },
                    "status": "accepted",
                })
        ihep_appt["participants"] = participants

        # Telehealth
        ihep_appt["ihep_virtual_visit"] = bool(
            athena_appt.get("telehealth")
            or athena_appt.get("appointmenttypeid") in ("telehealth", "video")
        )
        ihep_appt["ihep_telehealth_link"] = athena_appt.get("telehealthurl")

        # Department info
        if athena_appt.get("departmentid"):
            ihep_appt["location"] = {
                "reference": f"Location/athena-dept-{athena_appt['departmentid']}",
                "display": athena_appt.get("departmentname", ""),
            }

        ihep_appt["extensions"] = self._extract_extensions(athena_appt)
        return ihep_appt

    def map_bundle(self, athena_bundle: Dict) -> List[Dict]:
        """Process a FHIR Bundle and map each entry."""
        results = []

        if athena_bundle.get("resourceType") != "Bundle":
            resource_type = athena_bundle.get("resourceType", "")
            mapped = self._map_by_type(resource_type, athena_bundle)
            if mapped:
                results.append(mapped)
            return results

        for entry in athena_bundle.get("entry", []):
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType", "")
            try:
                mapped = self._map_by_type(resource_type, resource)
                if mapped:
                    results.append(mapped)
            except Exception as e:
                logger.warning(f"Failed to map athena {resource_type}: {e}")

        return results

    def _map_by_type(self, resource_type: str, resource: Dict) -> Optional[Dict]:
        mapper_map = {
            "Patient": self.map_patient,
            "Observation": self.map_observation,
            "Appointment": self.map_appointment,
        }
        mapper = mapper_map.get(resource_type)
        return mapper(resource) if mapper else None

    def _normalize_gender(self, gender: str) -> str:
        if not gender:
            return "unknown"
        g = gender.lower()
        if g in ("male", "m"):
            return "male"
        if g in ("female", "f"):
            return "female"
        if g in ("other", "o"):
            return "other"
        return "unknown"

    def _format_athena_date(self, date_str: str) -> Optional[str]:
        """Convert athena date format (MM/DD/YYYY) to FHIR date (YYYY-MM-DD)."""
        if not date_str:
            return None
        parts = date_str.split("/")
        if len(parts) == 3:
            return f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
        return date_str

    def _format_athena_datetime(
        self, date_str: str, time_str: str
    ) -> Optional[str]:
        """Combine athena date and time into ISO format."""
        date = self._format_athena_date(date_str)
        if not date:
            return None
        if time_str:
            # athena time format: HH:MM
            return f"{date}T{time_str}:00Z"
        return date

    def _map_athena_appointment_status(self, status: str) -> str:
        """Map athena appointment status to FHIR status."""
        status_map = {
            "booked": "booked",
            "confirmed": "booked",
            "checked-in": "arrived",
            "checked in": "arrived",
            "in progress": "arrived",
            "completed": "fulfilled",
            "cancelled": "cancelled",
            "canceled": "cancelled",
            "no-show": "noshow",
            "noshow": "noshow",
            "open": "proposed",
        }
        if not status:
            return "proposed"
        return status_map.get(status.lower(), status.lower())

    def _extract_identifier_type(self, identifier: Dict) -> str:
        type_obj = identifier.get("type", {})
        coding = type_obj.get("coding", [{}])
        if coding:
            return coding[0].get("code", "unknown")
        return "unknown"

    def _get_participant_type(self, participant: Dict) -> str:
        types = participant.get("type", [])
        if types:
            coding = types[0].get("coding", [{}])
            if coding:
                return coding[0].get("code", "unknown")
        return "unknown"

    def _extract_extensions(self, resource: Dict) -> List[Dict]:
        extensions = []
        for ext in resource.get("extension", []):
            extensions.append({
                "url": ext.get("url", ""),
                "value": (
                    ext.get("valueString")
                    or ext.get("valueCode")
                    or ext.get("valueBoolean")
                ),
                "vendor": "athenahealth",
            })
        return extensions
