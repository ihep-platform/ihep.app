/**
 * HL7 v2.x to FHIR R4 Converter
 *
 * Converts parsed HL7 v2.x messages to FHIR R4 resources.
 * Supports ADT (Admit/Discharge/Transfer), ORU (Results),
 * and SIU (Scheduling) message types.
 *
 * Author: Jason M Jarmacz | Co-Author: Claude by Anthropic
 */

/**
 * Convert HL7 v2.x XML (Mirth parsed) to a simplified JSON structure.
 */
function convertHL7XmlToJson(hl7Xml) {
    // Mirth provides HL7 as E4X XML; convert to workable JSON
    var result = {};

    try {
        if (typeof hl7Xml === 'string') {
            hl7Xml = new XML(hl7Xml);
        }

        // Extract segments
        var segments = ['MSH', 'EVN', 'PID', 'PV1', 'PV2', 'NK1', 'OBR', 'OBX', 'SCH', 'AIS', 'AIP', 'AIL'];
        for (var i = 0; i < segments.length; i++) {
            var segName = segments[i];
            var segList = hl7Xml[segName];
            if (segList && segList.length() > 0) {
                if (segList.length() === 1) {
                    result[segName] = parseSegmentToJson(segList[0], segName);
                } else {
                    result[segName] = [];
                    for (var j = 0; j < segList.length(); j++) {
                        result[segName].push(parseSegmentToJson(segList[j], segName));
                    }
                }
            }
        }
    } catch (e) {
        logger.error('Error converting HL7 XML to JSON: ' + e.message);
    }

    return result;
}

/**
 * Parse a single HL7 segment XML element to JSON.
 */
function parseSegmentToJson(segXml, segName) {
    var result = {};
    var children = segXml.children();
    for (var i = 0; i < children.length(); i++) {
        var child = children[i];
        var fieldName = child.localName();
        var components = child.children();
        if (components.length() > 1) {
            result[fieldName] = {};
            for (var j = 0; j < components.length(); j++) {
                var comp = components[j];
                result[fieldName][comp.localName()] = comp.toString();
            }
        } else {
            result[fieldName] = child.toString();
        }
    }
    return result;
}

/**
 * Main entry: convert a parsed HL7 v2.x message to a FHIR R4 Bundle.
 *
 * @param {Object} hl7Json - Parsed HL7 v2.x message as JSON
 * @param {string} messageType - Message type (e.g., 'ADT^A01', 'ORU^R01', 'SIU^S12')
 * @returns {Object} FHIR R4 Bundle
 */
function convertHL7v2ToFhir(hl7Json, messageType) {
    var bundle = {
        resourceType: 'Bundle',
        type: 'transaction',
        timestamp: new Date().toISOString(),
        entry: []
    };

    var msgParts = messageType.split('^');
    var msgCode = msgParts[0];
    var triggerEvent = msgParts.length > 1 ? msgParts[1] : '';

    switch (msgCode) {
        case 'ADT':
            convertADT(hl7Json, triggerEvent, bundle);
            break;
        case 'ORU':
            convertORU(hl7Json, triggerEvent, bundle);
            break;
        case 'SIU':
            convertSIU(hl7Json, triggerEvent, bundle);
            break;
        default:
            logger.warn('Unsupported HL7 message type: ' + messageType);
    }

    return bundle;
}

// =============================================================================
// ADT Message Conversion (Patient Administration)
// =============================================================================

/**
 * Convert ADT messages to Patient + Encounter FHIR resources.
 * Supports A01 (Admit), A03 (Discharge), A08 (Update).
 */
function convertADT(hl7Json, triggerEvent, bundle) {
    // Always create a Patient resource from PID
    if (hl7Json.PID) {
        var patient = convertPIDToPatient(hl7Json.PID);
        bundle.entry.push({
            resource: patient,
            request: {
                method: triggerEvent === 'A01' ? 'POST' : 'PUT',
                url: 'Patient/' + patient.id
            }
        });
    }

    // Create Encounter from PV1
    if (hl7Json.PV1) {
        var encounter = convertPV1ToEncounter(hl7Json.PV1, hl7Json.PID, triggerEvent);
        bundle.entry.push({
            resource: encounter,
            request: {
                method: 'POST',
                url: 'Encounter/' + encounter.id
            }
        });
    }
}

/**
 * Convert PID segment to FHIR Patient resource.
 */
function convertPIDToPatient(pid) {
    var patient = {
        resourceType: 'Patient',
        id: generateResourceId('Patient', getField(pid, 'PID.3')),
        active: true,
        identifier: [],
        name: [],
        telecom: [],
        address: []
    };

    // PID-3: Patient Identifier List (CX data type)
    var pid3 = getField(pid, 'PID.3');
    if (pid3) {
        var idValue = typeof pid3 === 'object' ? (pid3['PID.3.1'] || pid3['CX.1'] || '') : pid3;
        var idSystem = typeof pid3 === 'object' ? (pid3['PID.3.4'] || pid3['CX.4'] || '') : '';
        patient.identifier.push({
            use: 'usual',
            type: {
                coding: [{
                    system: 'http://terminology.hl7.org/CodeSystem/v2-0203',
                    code: 'MR',
                    display: 'Medical Record Number'
                }]
            },
            system: idSystem || 'urn:oid:2.16.840.1.113883.4.1',
            value: idValue
        });
    }

    // PID-5: Patient Name (XPN data type)
    var pid5 = getField(pid, 'PID.5');
    if (pid5) {
        var familyName = typeof pid5 === 'object' ? (pid5['PID.5.1'] || pid5['XPN.1'] || '') : pid5;
        var givenName = typeof pid5 === 'object' ? (pid5['PID.5.2'] || pid5['XPN.2'] || '') : '';
        var middleName = typeof pid5 === 'object' ? (pid5['PID.5.3'] || pid5['XPN.3'] || '') : '';
        var prefix = typeof pid5 === 'object' ? (pid5['PID.5.5'] || pid5['XPN.5'] || '') : '';
        var suffix = typeof pid5 === 'object' ? (pid5['PID.5.4'] || pid5['XPN.4'] || '') : '';

        var name = {
            use: 'official',
            family: familyName,
            given: []
        };
        if (givenName) name.given.push(givenName);
        if (middleName) name.given.push(middleName);
        if (prefix) name.prefix = [prefix];
        if (suffix) name.suffix = [suffix];
        patient.name.push(name);
    }

    // PID-7: Date of Birth
    var pid7 = getField(pid, 'PID.7');
    if (pid7) {
        patient.birthDate = formatHL7Date(typeof pid7 === 'object' ? (pid7['PID.7.1'] || '') : pid7);
    }

    // PID-8: Administrative Sex
    var pid8 = getField(pid, 'PID.8');
    if (pid8) {
        var sex = (typeof pid8 === 'object' ? (pid8['PID.8.1'] || '') : pid8).toUpperCase();
        if (sex === 'M') patient.gender = 'male';
        else if (sex === 'F') patient.gender = 'female';
        else if (sex === 'O') patient.gender = 'other';
        else patient.gender = 'unknown';
    }

    // PID-11: Patient Address (XAD data type)
    var pid11 = getField(pid, 'PID.11');
    if (pid11) {
        var addr = {
            use: 'home',
            type: 'physical',
            line: []
        };
        if (typeof pid11 === 'object') {
            if (pid11['PID.11.1'] || pid11['XAD.1']) addr.line.push(pid11['PID.11.1'] || pid11['XAD.1']);
            if (pid11['PID.11.2'] || pid11['XAD.2']) addr.line.push(pid11['PID.11.2'] || pid11['XAD.2']);
            addr.city = pid11['PID.11.3'] || pid11['XAD.3'] || '';
            addr.state = pid11['PID.11.4'] || pid11['XAD.4'] || '';
            addr.postalCode = pid11['PID.11.5'] || pid11['XAD.5'] || '';
            addr.country = pid11['PID.11.6'] || pid11['XAD.6'] || 'US';
        }
        patient.address.push(addr);
    }

    // PID-13: Phone Number - Home
    var pid13 = getField(pid, 'PID.13');
    if (pid13) {
        patient.telecom.push({
            system: 'phone',
            value: typeof pid13 === 'object' ? (pid13['PID.13.1'] || '') : pid13,
            use: 'home'
        });
    }

    // PID-14: Phone Number - Business
    var pid14 = getField(pid, 'PID.14');
    if (pid14) {
        patient.telecom.push({
            system: 'phone',
            value: typeof pid14 === 'object' ? (pid14['PID.14.1'] || '') : pid14,
            use: 'work'
        });
    }

    return patient;
}

/**
 * Convert PV1 segment to FHIR Encounter resource.
 */
function convertPV1ToEncounter(pv1, pid, triggerEvent) {
    var patientId = '';
    if (pid) {
        var pid3 = getField(pid, 'PID.3');
        patientId = typeof pid3 === 'object' ? (pid3['PID.3.1'] || '') : (pid3 || '');
    }

    var encounter = {
        resourceType: 'Encounter',
        id: generateResourceId('Encounter', getField(pv1, 'PV1.19') || new Date().getTime()),
        status: mapEncounterStatus(triggerEvent),
        class: mapPatientClass(getField(pv1, 'PV1.2')),
        subject: {
            reference: 'Patient/' + generateResourceId('Patient', getField(pid, 'PID.3'))
        },
        period: {}
    };

    // PV1-44: Admit Date/Time
    var pv144 = getField(pv1, 'PV1.44');
    if (pv144) {
        encounter.period.start = formatHL7DateTime(typeof pv144 === 'object' ? (pv144['PV1.44.1'] || '') : pv144);
    }

    // PV1-45: Discharge Date/Time
    var pv145 = getField(pv1, 'PV1.45');
    if (pv145) {
        encounter.period.end = formatHL7DateTime(typeof pv145 === 'object' ? (pv145['PV1.45.1'] || '') : pv145);
    }

    // PV1-3: Assigned Patient Location
    var pv13 = getField(pv1, 'PV1.3');
    if (pv13) {
        encounter.location = [{
            location: {
                display: typeof pv13 === 'object' ?
                    [pv13['PV1.3.1'], pv13['PV1.3.2'], pv13['PV1.3.3']].filter(Boolean).join(' - ') :
                    pv13
            },
            status: 'active'
        }];
    }

    // PV1-7: Attending Doctor
    var pv17 = getField(pv1, 'PV1.7');
    if (pv17) {
        encounter.participant = [{
            type: [{
                coding: [{
                    system: 'http://terminology.hl7.org/CodeSystem/v3-ParticipationType',
                    code: 'ATND',
                    display: 'attender'
                }]
            }],
            individual: {
                display: typeof pv17 === 'object' ?
                    [pv17['PV1.7.2'] || pv17['XCN.2'], pv17['PV1.7.3'] || pv17['XCN.3']].filter(Boolean).join(' ') :
                    pv17
            }
        }];
    }

    return encounter;
}

// =============================================================================
// ORU Message Conversion (Observation Results)
// =============================================================================

/**
 * Convert ORU^R01 to Observation + DiagnosticReport FHIR resources.
 */
function convertORU(hl7Json, triggerEvent, bundle) {
    // Create Patient from PID if present
    if (hl7Json.PID) {
        var patient = convertPIDToPatient(hl7Json.PID);
        bundle.entry.push({
            resource: patient,
            request: { method: 'PUT', url: 'Patient/' + patient.id }
        });
    }

    // Process OBX segments (observations)
    var obxSegments = hl7Json.OBX;
    if (obxSegments) {
        if (!Array.isArray(obxSegments)) obxSegments = [obxSegments];

        for (var i = 0; i < obxSegments.length; i++) {
            var observation = convertOBXToObservation(obxSegments[i], hl7Json.PID, hl7Json.OBR);
            bundle.entry.push({
                resource: observation,
                request: { method: 'POST', url: 'Observation' }
            });
        }
    }

    // Create DiagnosticReport from OBR if present
    if (hl7Json.OBR) {
        var report = convertOBRToDiagnosticReport(hl7Json.OBR, hl7Json.PID, obxSegments);
        bundle.entry.push({
            resource: report,
            request: { method: 'POST', url: 'DiagnosticReport' }
        });
    }
}

/**
 * Convert OBX segment to FHIR Observation.
 */
function convertOBXToObservation(obx, pid, obr) {
    var observation = {
        resourceType: 'Observation',
        id: generateResourceId('Observation', getField(obx, 'OBX.3') + '-' + (getField(obx, 'OBX.1') || Date.now())),
        status: mapObservationStatus(getField(obx, 'OBX.11'))
    };

    // OBX-3: Observation Identifier (CE/CWE)
    var obx3 = getField(obx, 'OBX.3');
    if (obx3) {
        observation.code = {
            coding: [{
                system: typeof obx3 === 'object' ? (obx3['OBX.3.3'] || 'http://loinc.org') : 'http://loinc.org',
                code: typeof obx3 === 'object' ? (obx3['OBX.3.1'] || '') : obx3,
                display: typeof obx3 === 'object' ? (obx3['OBX.3.2'] || '') : ''
            }]
        };
    }

    // Subject reference
    if (pid) {
        observation.subject = {
            reference: 'Patient/' + generateResourceId('Patient', getField(pid, 'PID.3'))
        };
    }

    // OBX-5: Observation Value
    var obx2 = getField(obx, 'OBX.2'); // Value type
    var obx5 = getField(obx, 'OBX.5');
    var valueType = typeof obx2 === 'object' ? (obx2['OBX.2.1'] || 'ST') : (obx2 || 'ST');

    if (obx5) {
        var val = typeof obx5 === 'object' ? (obx5['OBX.5.1'] || '') : obx5;

        switch (valueType.toUpperCase()) {
            case 'NM': // Numeric
                var obx6 = getField(obx, 'OBX.6');
                observation.valueQuantity = {
                    value: parseFloat(val),
                    unit: typeof obx6 === 'object' ? (obx6['OBX.6.1'] || '') : (obx6 || ''),
                    system: 'http://unitsofmeasure.org'
                };
                break;
            case 'ST': // String
            case 'TX': // Text
            case 'FT': // Formatted text
                observation.valueString = val;
                break;
            case 'CE': // Coded entry
            case 'CWE': // Coded with exceptions
                observation.valueCodeableConcept = {
                    coding: [{
                        code: val,
                        display: typeof obx5 === 'object' ? (obx5['OBX.5.2'] || '') : '',
                        system: typeof obx5 === 'object' ? (obx5['OBX.5.3'] || '') : ''
                    }]
                };
                break;
            case 'DT': // Date
            case 'TS': // Timestamp
                observation.valueDateTime = formatHL7DateTime(val);
                break;
            default:
                observation.valueString = val;
        }
    }

    // OBX-7: Reference Range
    var obx7 = getField(obx, 'OBX.7');
    if (obx7) {
        var rangeStr = typeof obx7 === 'object' ? (obx7['OBX.7.1'] || '') : obx7;
        observation.referenceRange = [{ text: rangeStr }];

        // Try to parse numeric range (e.g., "3.5-5.0")
        var rangeParts = rangeStr.split('-');
        if (rangeParts.length === 2) {
            var low = parseFloat(rangeParts[0]);
            var high = parseFloat(rangeParts[1]);
            if (!isNaN(low) && !isNaN(high)) {
                observation.referenceRange[0].low = { value: low };
                observation.referenceRange[0].high = { value: high };
            }
        }
    }

    // OBX-8: Abnormal Flags
    var obx8 = getField(obx, 'OBX.8');
    if (obx8) {
        var flag = typeof obx8 === 'object' ? (obx8['OBX.8.1'] || '') : obx8;
        observation.interpretation = [{
            coding: [{
                system: 'http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation',
                code: mapAbnormalFlag(flag),
                display: mapAbnormalFlagDisplay(flag)
            }]
        }];
    }

    // OBX-14: Observation DateTime
    var obx14 = getField(obx, 'OBX.14');
    if (obx14) {
        observation.effectiveDateTime = formatHL7DateTime(typeof obx14 === 'object' ? (obx14['OBX.14.1'] || '') : obx14);
    }

    return observation;
}

/**
 * Convert OBR segment to FHIR DiagnosticReport.
 */
function convertOBRToDiagnosticReport(obr, pid, obxSegments) {
    var obrData = Array.isArray(obr) ? obr[0] : obr;

    var report = {
        resourceType: 'DiagnosticReport',
        id: generateResourceId('DiagnosticReport', getField(obrData, 'OBR.3') || Date.now()),
        status: 'final'
    };

    // OBR-4: Universal Service Identifier
    var obr4 = getField(obrData, 'OBR.4');
    if (obr4) {
        report.code = {
            coding: [{
                system: typeof obr4 === 'object' ? (obr4['OBR.4.3'] || '') : '',
                code: typeof obr4 === 'object' ? (obr4['OBR.4.1'] || '') : obr4,
                display: typeof obr4 === 'object' ? (obr4['OBR.4.2'] || '') : ''
            }]
        };
    }

    if (pid) {
        report.subject = {
            reference: 'Patient/' + generateResourceId('Patient', getField(pid, 'PID.3'))
        };
    }

    // OBR-7: Observation Date/Time
    var obr7 = getField(obrData, 'OBR.7');
    if (obr7) {
        report.effectiveDateTime = formatHL7DateTime(typeof obr7 === 'object' ? (obr7['OBR.7.1'] || '') : obr7);
    }

    // OBR-22: Results Report/Status Change Date
    var obr22 = getField(obrData, 'OBR.22');
    if (obr22) {
        report.issued = formatHL7DateTime(typeof obr22 === 'object' ? (obr22['OBR.22.1'] || '') : obr22);
    }

    // Reference observations
    if (obxSegments) {
        var obxArr = Array.isArray(obxSegments) ? obxSegments : [obxSegments];
        report.result = [];
        for (var i = 0; i < obxArr.length; i++) {
            report.result.push({
                reference: 'Observation/' + generateResourceId('Observation',
                    getField(obxArr[i], 'OBX.3') + '-' + (getField(obxArr[i], 'OBX.1') || i))
            });
        }
    }

    return report;
}

// =============================================================================
// SIU Message Conversion (Scheduling)
// =============================================================================

/**
 * Convert SIU^S12 to FHIR Appointment resource.
 */
function convertSIU(hl7Json, triggerEvent, bundle) {
    // Patient
    if (hl7Json.PID) {
        var patient = convertPIDToPatient(hl7Json.PID);
        bundle.entry.push({
            resource: patient,
            request: { method: 'PUT', url: 'Patient/' + patient.id }
        });
    }

    // Appointment from SCH segment
    if (hl7Json.SCH) {
        var schData = Array.isArray(hl7Json.SCH) ? hl7Json.SCH[0] : hl7Json.SCH;
        var appointment = {
            resourceType: 'Appointment',
            id: generateResourceId('Appointment', getField(schData, 'SCH.1') || Date.now()),
            status: mapAppointmentStatus(triggerEvent),
            participant: []
        };

        // SCH-7: Appointment Reason
        var sch7 = getField(schData, 'SCH.7');
        if (sch7) {
            appointment.reasonCode = [{
                coding: [{
                    code: typeof sch7 === 'object' ? (sch7['SCH.7.1'] || '') : sch7,
                    display: typeof sch7 === 'object' ? (sch7['SCH.7.2'] || '') : ''
                }]
            }];
        }

        // SCH-11: Appointment Timing (start/duration)
        var sch11 = getField(schData, 'SCH.11');
        if (sch11) {
            var startTime = typeof sch11 === 'object' ? (sch11['SCH.11.4'] || sch11['SCH.11.1'] || '') : sch11;
            if (startTime) {
                appointment.start = formatHL7DateTime(startTime);
            }
            var duration = typeof sch11 === 'object' ? (sch11['SCH.11.3'] || '') : '';
            if (duration) {
                appointment.minutesDuration = parseInt(duration) || null;
                if (appointment.start && appointment.minutesDuration) {
                    var endDate = new Date(appointment.start);
                    endDate.setMinutes(endDate.getMinutes() + appointment.minutesDuration);
                    appointment.end = endDate.toISOString();
                }
            }
        }

        // SCH-25: Filler Status Code
        var sch25 = getField(schData, 'SCH.25');
        if (sch25) {
            var statusCode = typeof sch25 === 'object' ? (sch25['SCH.25.1'] || '') : sch25;
            appointment.status = mapFillerStatus(statusCode) || appointment.status;
        }

        // Patient participant
        if (hl7Json.PID) {
            appointment.participant.push({
                actor: {
                    reference: 'Patient/' + generateResourceId('Patient', getField(hl7Json.PID, 'PID.3'))
                },
                required: 'required',
                status: 'accepted'
            });
        }

        // Provider from AIP segment
        if (hl7Json.AIP) {
            var aipData = Array.isArray(hl7Json.AIP) ? hl7Json.AIP[0] : hl7Json.AIP;
            var aip3 = getField(aipData, 'AIP.3');
            if (aip3) {
                appointment.participant.push({
                    type: [{
                        coding: [{
                            system: 'http://terminology.hl7.org/CodeSystem/v3-ParticipationType',
                            code: 'PPRF',
                            display: 'primary performer'
                        }]
                    }],
                    actor: {
                        display: typeof aip3 === 'object' ?
                            [aip3['AIP.3.2'] || aip3['XCN.2'], aip3['AIP.3.3'] || aip3['XCN.3']].filter(Boolean).join(' ') :
                            aip3
                    },
                    required: 'required',
                    status: 'accepted'
                });
            }
        }

        // Location from AIL segment
        if (hl7Json.AIL) {
            var ailData = Array.isArray(hl7Json.AIL) ? hl7Json.AIL[0] : hl7Json.AIL;
            var ail3 = getField(ailData, 'AIL.3');
            if (ail3) {
                appointment.participant.push({
                    type: [{
                        coding: [{
                            system: 'http://terminology.hl7.org/CodeSystem/v3-ParticipationType',
                            code: 'LOC',
                            display: 'location'
                        }]
                    }],
                    actor: {
                        display: typeof ail3 === 'object' ? (ail3['AIL.3.1'] || '') : ail3
                    },
                    required: 'required',
                    status: 'accepted'
                });
            }
        }

        bundle.entry.push({
            resource: appointment,
            request: { method: 'POST', url: 'Appointment' }
        });
    }
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Safely get a field from a parsed HL7 segment.
 */
function getField(segment, fieldPath) {
    if (!segment) return null;
    return segment[fieldPath] || null;
}

/**
 * Generate a deterministic FHIR resource ID from source data.
 */
function generateResourceId(resourceType, sourceValue) {
    var raw = String(sourceValue || Date.now());
    if (typeof raw === 'object') {
        raw = JSON.stringify(raw);
    }
    var hash = 0;
    for (var i = 0; i < raw.length; i++) {
        var char = raw.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    return resourceType.toLowerCase() + '-' + Math.abs(hash).toString(36);
}

/**
 * Format HL7 date (YYYYMMDD) to FHIR date (YYYY-MM-DD).
 */
function formatHL7Date(hl7Date) {
    if (!hl7Date || hl7Date.length < 8) return null;
    var d = String(hl7Date);
    return d.substring(0, 4) + '-' + d.substring(4, 6) + '-' + d.substring(6, 8);
}

/**
 * Format HL7 datetime (YYYYMMDDHHMMSS) to ISO 8601.
 */
function formatHL7DateTime(hl7DateTime) {
    if (!hl7DateTime) return null;
    var d = String(hl7DateTime);
    if (d.length < 8) return null;

    var result = d.substring(0, 4) + '-' + d.substring(4, 6) + '-' + d.substring(6, 8);
    if (d.length >= 12) {
        result += 'T' + d.substring(8, 10) + ':' + d.substring(10, 12);
        if (d.length >= 14) {
            result += ':' + d.substring(12, 14);
        } else {
            result += ':00';
        }
        result += 'Z';
    }
    return result;
}

/**
 * Map ADT trigger event to FHIR Encounter status.
 */
function mapEncounterStatus(triggerEvent) {
    var statusMap = {
        'A01': 'in-progress',   // Admit
        'A02': 'in-progress',   // Transfer
        'A03': 'finished',      // Discharge
        'A04': 'arrived',       // Register
        'A08': 'in-progress',   // Update
        'A11': 'cancelled',     // Cancel admit
        'A13': 'cancelled'      // Cancel discharge
    };
    return statusMap[triggerEvent] || 'unknown';
}

/**
 * Map PV1-2 Patient Class to FHIR Encounter class.
 */
function mapPatientClass(patientClass) {
    var val = typeof patientClass === 'object' ? (patientClass['PV1.2.1'] || '') : (patientClass || '');
    var classMap = {
        'I': { system: 'http://terminology.hl7.org/CodeSystem/v3-ActCode', code: 'IMP', display: 'inpatient encounter' },
        'O': { system: 'http://terminology.hl7.org/CodeSystem/v3-ActCode', code: 'AMB', display: 'ambulatory' },
        'E': { system: 'http://terminology.hl7.org/CodeSystem/v3-ActCode', code: 'EMER', display: 'emergency' },
        'P': { system: 'http://terminology.hl7.org/CodeSystem/v3-ActCode', code: 'PRENC', display: 'pre-admission' }
    };
    return classMap[val.toUpperCase()] || { system: 'http://terminology.hl7.org/CodeSystem/v3-ActCode', code: 'AMB', display: 'ambulatory' };
}

/**
 * Map OBX-11 Observation Result Status to FHIR status.
 */
function mapObservationStatus(status) {
    var val = typeof status === 'object' ? (status['OBX.11.1'] || '') : (status || '');
    var statusMap = {
        'F': 'final',
        'P': 'preliminary',
        'C': 'corrected',
        'R': 'registered',
        'I': 'registered',
        'S': 'preliminary',
        'X': 'cancelled',
        'W': 'entered-in-error'
    };
    return statusMap[val.toUpperCase()] || 'unknown';
}

/**
 * Map SIU trigger event to FHIR Appointment status.
 */
function mapAppointmentStatus(triggerEvent) {
    var statusMap = {
        'S12': 'booked',        // New appointment
        'S13': 'booked',        // Rescheduled
        'S14': 'cancelled',     // Cancelled
        'S15': 'cancelled',     // Discontinued
        'S17': 'noshow',        // No-show
        'S26': 'arrived'        // Patient arrived
    };
    return statusMap[triggerEvent] || 'proposed';
}

/**
 * Map SCH-25 Filler Status to FHIR Appointment status.
 */
function mapFillerStatus(fillerStatus) {
    if (!fillerStatus) return null;
    var statusMap = {
        'BOOKED': 'booked',
        'STARTED': 'arrived',
        'COMPLETE': 'fulfilled',
        'CANCELLED': 'cancelled',
        'NOSHOW': 'noshow',
        'WAITLIST': 'waitlist'
    };
    return statusMap[fillerStatus.toUpperCase()] || null;
}

/**
 * Map HL7 abnormal flags to FHIR interpretation codes.
 */
function mapAbnormalFlag(flag) {
    var flagMap = {
        'H': 'H', 'L': 'L', 'HH': 'HH', 'LL': 'LL',
        'A': 'A', 'N': 'N', 'U': 'U', 'D': 'D',
        '>': 'H', '<': 'L'
    };
    return flagMap[flag] || flag;
}

/**
 * Map abnormal flag to display text.
 */
function mapAbnormalFlagDisplay(flag) {
    var displayMap = {
        'H': 'High', 'L': 'Low', 'HH': 'Critical high', 'LL': 'Critical low',
        'A': 'Abnormal', 'N': 'Normal', 'U': 'Significant change up',
        'D': 'Significant change down'
    };
    return displayMap[flag] || flag;
}
