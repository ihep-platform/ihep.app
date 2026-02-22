/**
 * FHIR R4 to IHEP Canonical Format Transformer
 *
 * Normalizes incoming FHIR R4 resources from any vendor
 * (Epic, Cerner, Allscripts, athenahealth) into the IHEP
 * canonical data format for unified storage and processing.
 *
 * Author: Jason M Jarmacz | Co-Author: Claude by Anthropic
 */

/**
 * Main entry point: transform a FHIR resource or bundle to IHEP format.
 *
 * @param {Object} fhirData - FHIR R4 Bundle or individual Resource
 * @param {string} vendor - Source vendor identifier (epic, cerner, allscripts, athenahealth)
 * @returns {Object} IHEP canonical format envelope
 */
function transformFhirToIhep(fhirData, vendor) {
    var result = {
        ihep_version: '1.0',
        source_vendor: vendor,
        transformed_at: new Date().toISOString(),
        resources: []
    };

    if (fhirData.resourceType === 'Bundle' && fhirData.entry) {
        for (var i = 0; i < fhirData.entry.length; i++) {
            var entry = fhirData.entry[i];
            if (entry.resource) {
                var transformed = transformResource(entry.resource, vendor);
                if (transformed) {
                    result.resources.push(transformed);
                }
            }
        }
    } else if (fhirData.resourceType) {
        var transformed = transformResource(fhirData, vendor);
        if (transformed) {
            result.resources.push(transformed);
        }
    }

    result.resource_count = result.resources.length;
    return result;
}

/**
 * Route a FHIR resource to its appropriate transformer.
 */
function transformResource(resource, vendor) {
    switch (resource.resourceType) {
        case 'Patient':
            return transformPatient(resource, vendor);
        case 'Observation':
            return transformObservation(resource, vendor);
        case 'Appointment':
            return transformAppointment(resource, vendor);
        case 'CarePlan':
            return transformCarePlan(resource, vendor);
        case 'Encounter':
            return transformEncounter(resource, vendor);
        case 'DiagnosticReport':
            return transformDiagnosticReport(resource, vendor);
        default:
            // Pass through unknown resource types with metadata
            return {
                ihep_resource_type: resource.resourceType,
                ihep_id: generateIhepId(resource.resourceType, resource.id, vendor),
                source_vendor: vendor,
                source_resource_type: resource.resourceType,
                source_id: resource.id || null,
                raw_resource: resource,
                transformed_at: new Date().toISOString()
            };
    }
}

/**
 * Transform FHIR Patient to IHEP canonical Patient.
 */
function transformPatient(patient, vendor) {
    var ihepPatient = {
        ihep_resource_type: 'Patient',
        ihep_id: generateIhepId('Patient', patient.id, vendor),
        source_vendor: vendor,
        source_id: patient.id || null,
        active: patient.active !== false,
        transformed_at: new Date().toISOString()
    };

    // Name normalization
    ihepPatient.name = [];
    if (patient.name && patient.name.length > 0) {
        for (var i = 0; i < patient.name.length; i++) {
            var name = patient.name[i];
            ihepPatient.name.push({
                use: name.use || 'official',
                family: name.family || '',
                given: name.given || [],
                prefix: name.prefix || [],
                suffix: name.suffix || [],
                text: name.text || buildNameText(name)
            });
        }
    }

    // Demographics
    ihepPatient.birth_date = patient.birthDate || null;
    ihepPatient.gender = normalizeGender(patient.gender);
    ihepPatient.deceased = patient.deceasedBoolean || false;
    ihepPatient.deceased_date = patient.deceasedDateTime || null;

    // Identifiers (MRN, SSN, etc.)
    ihepPatient.identifiers = [];
    if (patient.identifier) {
        for (var i = 0; i < patient.identifier.length; i++) {
            var id = patient.identifier[i];
            ihepPatient.identifiers.push({
                system: id.system || '',
                value: id.value || '',
                type: extractIdentifierType(id),
                vendor_system: vendor
            });
        }
    }

    // Contact information
    ihepPatient.telecom = [];
    if (patient.telecom) {
        for (var i = 0; i < patient.telecom.length; i++) {
            var t = patient.telecom[i];
            ihepPatient.telecom.push({
                system: t.system || 'other',
                value: t.value || '',
                use: t.use || 'home',
                rank: t.rank || null
            });
        }
    }

    // Address
    ihepPatient.address = [];
    if (patient.address) {
        for (var i = 0; i < patient.address.length; i++) {
            var addr = patient.address[i];
            ihepPatient.address.push({
                use: addr.use || 'home',
                type: addr.type || 'physical',
                line: addr.line || [],
                city: addr.city || '',
                state: addr.state || '',
                postal_code: addr.postalCode || '',
                country: addr.country || 'US'
            });
        }
    }

    // Managing organization
    if (patient.managingOrganization) {
        ihepPatient.managing_organization = {
            reference: patient.managingOrganization.reference || '',
            display: patient.managingOrganization.display || ''
        };
    }

    // Vendor-specific extensions
    ihepPatient.extensions = extractVendorExtensions(patient, vendor);

    // IHEP metadata
    ihepPatient.meta = {
        source: vendor,
        last_updated: (patient.meta && patient.meta.lastUpdated) || new Date().toISOString(),
        version_id: (patient.meta && patient.meta.versionId) || '1'
    };

    return ihepPatient;
}

/**
 * Transform FHIR Observation to IHEP canonical Observation.
 */
function transformObservation(observation, vendor) {
    var ihepObs = {
        ihep_resource_type: 'Observation',
        ihep_id: generateIhepId('Observation', observation.id, vendor),
        source_vendor: vendor,
        source_id: observation.id || null,
        transformed_at: new Date().toISOString()
    };

    // Status
    ihepObs.status = observation.status || 'unknown';

    // Category (vital-signs, laboratory, etc.)
    ihepObs.category = [];
    if (observation.category) {
        for (var i = 0; i < observation.category.length; i++) {
            var cat = observation.category[i];
            if (cat.coding) {
                for (var j = 0; j < cat.coding.length; j++) {
                    ihepObs.category.push({
                        system: cat.coding[j].system || '',
                        code: cat.coding[j].code || '',
                        display: cat.coding[j].display || ''
                    });
                }
            }
        }
    }

    // Code (LOINC, SNOMED, etc.)
    ihepObs.code = normalizeCodeableConcept(observation.code);

    // Subject reference
    ihepObs.subject = observation.subject ? {
        reference: observation.subject.reference || '',
        display: observation.subject.display || ''
    } : null;

    // Effective date/time
    ihepObs.effective_date_time = observation.effectiveDateTime ||
        (observation.effectivePeriod && observation.effectivePeriod.start) || null;

    // Issued
    ihepObs.issued = observation.issued || null;

    // Value - handle different value types
    if (observation.valueQuantity) {
        ihepObs.value = {
            type: 'Quantity',
            value: observation.valueQuantity.value,
            unit: observation.valueQuantity.unit || '',
            system: observation.valueQuantity.system || 'http://unitsofmeasure.org',
            code: observation.valueQuantity.code || ''
        };
    } else if (observation.valueCodeableConcept) {
        ihepObs.value = {
            type: 'CodeableConcept',
            coding: normalizeCodeableConcept(observation.valueCodeableConcept)
        };
    } else if (observation.valueString !== undefined) {
        ihepObs.value = {
            type: 'String',
            value: observation.valueString
        };
    } else if (observation.valueBoolean !== undefined) {
        ihepObs.value = {
            type: 'Boolean',
            value: observation.valueBoolean
        };
    } else {
        ihepObs.value = null;
    }

    // Interpretation
    ihepObs.interpretation = observation.interpretation ?
        normalizeCodeableConcept(observation.interpretation[0]) : null;

    // Reference range
    ihepObs.reference_range = [];
    if (observation.referenceRange) {
        for (var i = 0; i < observation.referenceRange.length; i++) {
            var rr = observation.referenceRange[i];
            ihepObs.reference_range.push({
                low: rr.low ? rr.low.value : null,
                high: rr.high ? rr.high.value : null,
                unit: (rr.low && rr.low.unit) || (rr.high && rr.high.unit) || '',
                text: rr.text || ''
            });
        }
    }

    // Performer
    ihepObs.performer = [];
    if (observation.performer) {
        for (var i = 0; i < observation.performer.length; i++) {
            ihepObs.performer.push({
                reference: observation.performer[i].reference || '',
                display: observation.performer[i].display || ''
            });
        }
    }

    // IHEP extensions
    ihepObs.extensions = extractVendorExtensions(observation, vendor);
    ihepObs.ihep_data_quality_score = calculateDataQualityScore(ihepObs);
    ihepObs.ihep_source_system = vendor;

    ihepObs.meta = {
        source: vendor,
        last_updated: (observation.meta && observation.meta.lastUpdated) || new Date().toISOString()
    };

    return ihepObs;
}

/**
 * Transform FHIR Appointment to IHEP canonical Appointment.
 */
function transformAppointment(appointment, vendor) {
    var ihepAppt = {
        ihep_resource_type: 'Appointment',
        ihep_id: generateIhepId('Appointment', appointment.id, vendor),
        source_vendor: vendor,
        source_id: appointment.id || null,
        transformed_at: new Date().toISOString()
    };

    ihepAppt.status = appointment.status || 'proposed';
    ihepAppt.start = appointment.start || null;
    ihepAppt.end = appointment.end || null;
    ihepAppt.minutes_duration = appointment.minutesDuration || null;
    ihepAppt.description = appointment.description || '';
    ihepAppt.comment = appointment.comment || '';

    // Service type
    ihepAppt.service_type = [];
    if (appointment.serviceType) {
        for (var i = 0; i < appointment.serviceType.length; i++) {
            ihepAppt.service_type.push(normalizeCodeableConcept(appointment.serviceType[i]));
        }
    }

    // Reason
    ihepAppt.reason_code = [];
    if (appointment.reasonCode) {
        for (var i = 0; i < appointment.reasonCode.length; i++) {
            ihepAppt.reason_code.push(normalizeCodeableConcept(appointment.reasonCode[i]));
        }
    }

    // Participants
    ihepAppt.participants = [];
    if (appointment.participant) {
        for (var i = 0; i < appointment.participant.length; i++) {
            var p = appointment.participant[i];
            ihepAppt.participants.push({
                type: (p.type && p.type[0] && p.type[0].coding && p.type[0].coding[0]) ?
                    p.type[0].coding[0].code : 'unknown',
                actor: p.actor ? {
                    reference: p.actor.reference || '',
                    display: p.actor.display || ''
                } : null,
                status: p.status || 'accepted',
                required: p.required || 'required'
            });
        }
    }

    // IHEP extensions for telehealth
    ihepAppt.ihep_virtual_visit = false;
    ihepAppt.ihep_telehealth_link = null;

    var extensions = extractVendorExtensions(appointment, vendor);
    if (extensions) {
        for (var i = 0; i < extensions.length; i++) {
            var ext = extensions[i];
            if (ext.url && (ext.url.indexOf('telehealth') !== -1 || ext.url.indexOf('virtual') !== -1)) {
                ihepAppt.ihep_virtual_visit = true;
                if (ext.valueUrl || ext.valueString) {
                    ihepAppt.ihep_telehealth_link = ext.valueUrl || ext.valueString;
                }
            }
        }
    }

    ihepAppt.extensions = extensions;
    ihepAppt.meta = {
        source: vendor,
        last_updated: (appointment.meta && appointment.meta.lastUpdated) || new Date().toISOString()
    };

    return ihepAppt;
}

/**
 * Transform FHIR CarePlan to IHEP canonical CarePlan.
 */
function transformCarePlan(carePlan, vendor) {
    return {
        ihep_resource_type: 'CarePlan',
        ihep_id: generateIhepId('CarePlan', carePlan.id, vendor),
        source_vendor: vendor,
        source_id: carePlan.id || null,
        status: carePlan.status || 'unknown',
        intent: carePlan.intent || 'plan',
        title: carePlan.title || '',
        description: carePlan.description || '',
        subject: carePlan.subject ? {
            reference: carePlan.subject.reference || '',
            display: carePlan.subject.display || ''
        } : null,
        period: carePlan.period ? {
            start: carePlan.period.start || null,
            end: carePlan.period.end || null
        } : null,
        category: carePlan.category ? carePlan.category.map(function(c) {
            return normalizeCodeableConcept(c);
        }) : [],
        activity: carePlan.activity ? carePlan.activity.map(function(a) {
            return {
                detail: a.detail ? {
                    status: a.detail.status || 'unknown',
                    description: a.detail.description || '',
                    code: a.detail.code ? normalizeCodeableConcept(a.detail.code) : null
                } : null
            };
        }) : [],
        extensions: extractVendorExtensions(carePlan, vendor),
        transformed_at: new Date().toISOString(),
        meta: {
            source: vendor,
            last_updated: (carePlan.meta && carePlan.meta.lastUpdated) || new Date().toISOString()
        }
    };
}

/**
 * Transform FHIR Encounter to IHEP format.
 */
function transformEncounter(encounter, vendor) {
    return {
        ihep_resource_type: 'Encounter',
        ihep_id: generateIhepId('Encounter', encounter.id, vendor),
        source_vendor: vendor,
        source_id: encounter.id || null,
        status: encounter.status || 'unknown',
        class_code: encounter.class ? encounter.class.code || '' : '',
        type: encounter.type ? encounter.type.map(function(t) {
            return normalizeCodeableConcept(t);
        }) : [],
        subject: encounter.subject ? {
            reference: encounter.subject.reference || '',
            display: encounter.subject.display || ''
        } : null,
        period: encounter.period ? {
            start: encounter.period.start || null,
            end: encounter.period.end || null
        } : null,
        reason_code: encounter.reasonCode ? encounter.reasonCode.map(function(r) {
            return normalizeCodeableConcept(r);
        }) : [],
        extensions: extractVendorExtensions(encounter, vendor),
        transformed_at: new Date().toISOString(),
        meta: {
            source: vendor,
            last_updated: (encounter.meta && encounter.meta.lastUpdated) || new Date().toISOString()
        }
    };
}

/**
 * Transform FHIR DiagnosticReport to IHEP format.
 */
function transformDiagnosticReport(report, vendor) {
    return {
        ihep_resource_type: 'DiagnosticReport',
        ihep_id: generateIhepId('DiagnosticReport', report.id, vendor),
        source_vendor: vendor,
        source_id: report.id || null,
        status: report.status || 'unknown',
        code: normalizeCodeableConcept(report.code),
        subject: report.subject ? {
            reference: report.subject.reference || '',
            display: report.subject.display || ''
        } : null,
        effective_date_time: report.effectiveDateTime || null,
        issued: report.issued || null,
        result: report.result ? report.result.map(function(r) {
            return { reference: r.reference || '', display: r.display || '' };
        }) : [],
        conclusion: report.conclusion || '',
        extensions: extractVendorExtensions(report, vendor),
        transformed_at: new Date().toISOString(),
        meta: {
            source: vendor,
            last_updated: (report.meta && report.meta.lastUpdated) || new Date().toISOString()
        }
    };
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Generate a deterministic IHEP resource ID.
 */
function generateIhepId(resourceType, sourceId, vendor) {
    var raw = vendor + ':' + resourceType + ':' + (sourceId || 'unknown');
    // Simple hash for deterministic ID generation
    var hash = 0;
    for (var i = 0; i < raw.length; i++) {
        var char = raw.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32-bit integer
    }
    return 'ihep-' + resourceType.toLowerCase() + '-' + Math.abs(hash).toString(36);
}

/**
 * Normalize a FHIR CodeableConcept to a simplified structure.
 */
function normalizeCodeableConcept(codeableConcept) {
    if (!codeableConcept) return null;

    var result = {
        text: codeableConcept.text || '',
        coding: []
    };

    if (codeableConcept.coding) {
        for (var i = 0; i < codeableConcept.coding.length; i++) {
            var c = codeableConcept.coding[i];
            result.coding.push({
                system: normalizeCodeSystem(c.system || ''),
                code: c.code || '',
                display: c.display || ''
            });
        }
    }

    return result;
}

/**
 * Normalize code system URLs to standard identifiers.
 */
function normalizeCodeSystem(system) {
    var systemMap = {
        'http://loinc.org': 'LOINC',
        'http://snomed.info/sct': 'SNOMED-CT',
        'http://hl7.org/fhir/sid/icd-10-cm': 'ICD-10-CM',
        'http://hl7.org/fhir/sid/icd-10': 'ICD-10',
        'http://www.nlm.nih.gov/research/umls/rxnorm': 'RxNorm',
        'http://hl7.org/fhir/sid/cvx': 'CVX',
        'http://hl7.org/fhir/sid/ndc': 'NDC',
        'http://terminology.hl7.org/CodeSystem/observation-category': 'ObservationCategory',
        'http://unitsofmeasure.org': 'UCUM'
    };
    return systemMap[system] || system;
}

/**
 * Normalize gender values across vendors.
 */
function normalizeGender(gender) {
    if (!gender) return 'unknown';
    var g = gender.toLowerCase();
    if (g === 'male' || g === 'm') return 'male';
    if (g === 'female' || g === 'f') return 'female';
    if (g === 'other' || g === 'o') return 'other';
    return 'unknown';
}

/**
 * Build full name text from name components.
 */
function buildNameText(name) {
    var parts = [];
    if (name.prefix) parts = parts.concat(name.prefix);
    if (name.given) parts = parts.concat(name.given);
    if (name.family) parts.push(name.family);
    if (name.suffix) parts = parts.concat(name.suffix);
    return parts.join(' ');
}

/**
 * Extract identifier type from FHIR Identifier.
 */
function extractIdentifierType(identifier) {
    if (identifier.type && identifier.type.coding && identifier.type.coding.length > 0) {
        return identifier.type.coding[0].code || 'unknown';
    }
    // Infer from system
    if (identifier.system) {
        if (identifier.system.indexOf('MR') !== -1 || identifier.system.indexOf('mrn') !== -1) return 'MRN';
        if (identifier.system.indexOf('SSN') !== -1 || identifier.system.indexOf('ssn') !== -1) return 'SSN';
        if (identifier.system.indexOf('DL') !== -1) return 'DL';
    }
    return 'unknown';
}

/**
 * Extract vendor-specific extensions from a FHIR resource.
 */
function extractVendorExtensions(resource, vendor) {
    if (!resource.extension || resource.extension.length === 0) return [];

    return resource.extension.map(function(ext) {
        return {
            url: ext.url || '',
            value: ext.valueString || ext.valueCode || ext.valueBoolean ||
                   ext.valueInteger || ext.valueUrl || ext.valueReference || null,
            vendor: vendor
        };
    });
}

/**
 * Calculate a data quality score (0-100) for an observation.
 */
function calculateDataQualityScore(ihepObs) {
    var score = 0;
    var maxScore = 100;
    var checks = 0;
    var passed = 0;

    // Has a status
    checks++; if (ihepObs.status && ihepObs.status !== 'unknown') passed++;
    // Has a code
    checks++; if (ihepObs.code && ihepObs.code.coding && ihepObs.code.coding.length > 0) passed++;
    // Has a subject
    checks++; if (ihepObs.subject) passed++;
    // Has a value
    checks++; if (ihepObs.value) passed++;
    // Has an effective date
    checks++; if (ihepObs.effective_date_time) passed++;
    // Has standard coding (LOINC/SNOMED)
    checks++;
    if (ihepObs.code && ihepObs.code.coding) {
        for (var i = 0; i < ihepObs.code.coding.length; i++) {
            if (ihepObs.code.coding[i].system === 'LOINC' || ihepObs.code.coding[i].system === 'SNOMED-CT') {
                passed++;
                break;
            }
        }
    }

    return checks > 0 ? Math.round((passed / checks) * maxScore) : 0;
}
