{{/*
Expand the name of the chart.
*/}}
{{- define "claude-kit-api.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "claude-kit-api.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "claude-kit-api.labels" -}}
helm.sh/chart: {{ include "claude-kit-api.name" . }}-{{ .Chart.Version | replace "+" "_" }}
{{ include "claude-kit-api.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "claude-kit-api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "claude-kit-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
