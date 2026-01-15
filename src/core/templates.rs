//! Template engine for ADR generation.
//!
//! This module provides template rendering using Tera,
//! with built-in templates for common ADR formats.

use crate::Error;
use std::collections::HashMap;
use tera::{Context, Tera};

/// Built-in ADR template: Nygard format.
pub const TEMPLATE_NYGARD: &str = r#"# {{ title }}

## Status

{{ status }}

## Context

{{ context | default(value="What is the issue that we're seeing that is motivating this decision or change?") }}

## Decision

{{ decision | default(value="What is the change that we're proposing and/or doing?") }}

## Consequences

{{ consequences | default(value="What becomes easier or more difficult to do because of this change?") }}
"#;

/// Built-in ADR template: MADR format.
pub const TEMPLATE_MADR: &str = r#"# {{ title }}

## Status

{{ status }}

{% if deciders %}
Deciders: {{ deciders | join(sep=", ") }}
{% endif %}
{% if date %}
Date: {{ date }}
{% endif %}

## Context and Problem Statement

{{ context | default(value="Describe the context and problem statement...") }}

## Decision Drivers

{% for driver in decision_drivers | default(value=[]) %}
* {{ driver }}
{% else %}
* Driver 1
* Driver 2
{% endfor %}

## Considered Options

{% for option in options | default(value=[]) %}
* {{ option }}
{% else %}
* Option 1
* Option 2
{% endfor %}

## Decision Outcome

Chosen option: "{{ chosen_option | default(value="Option X") }}"

### Consequences

#### Good

{% for item in good_consequences | default(value=[]) %}
* {{ item }}
{% else %}
* Good consequence 1
{% endfor %}

#### Bad

{% for item in bad_consequences | default(value=[]) %}
* {{ item }}
{% else %}
* Bad consequence 1
{% endfor %}

## More Information

{{ more_info | default(value="Additional information, links, references...") }}
"#;

/// Built-in ADR template: Y-statement format.
pub const TEMPLATE_Y_STATEMENT: &str = r#"# {{ title }}

## Status

{{ status }}

## Decision

In the context of {{ context | default(value="<use case/user story>") }},
facing {{ facing | default(value="<concern>") }},
we decided for {{ decision | default(value="<option>") }}
and against {{ against | default(value="<other options>") }},
to achieve {{ achieve | default(value="<quality>") }},
accepting {{ accepting | default(value="<downside>") }}.
"#;

/// Built-in ADR template: Alexandrian format.
pub const TEMPLATE_ALEXANDRIAN: &str = r#"# {{ title }}

## Status

{{ status }}

## Prologue

{{ prologue | default(value="Summary and context for this ADR") }}

## Problem Statement

{{ problem | default(value="The problem or question being addressed") }}

## Forces

{% for force in forces | default(value=[]) %}
* {{ force }}
{% else %}
* Force 1: Description
* Force 2: Description
{% endfor %}

## Solution

{{ solution | default(value="The chosen solution") }}

## Consequences

{{ consequences | default(value="Resulting context after applying the solution") }}

## Related Patterns

{% for pattern in related | default(value=[]) %}
* {{ pattern }}
{% endfor %}
"#;

/// Built-in ADR template: Business Case format.
pub const TEMPLATE_BUSINESS_CASE: &str = r#"# {{ title }}

## Status

{{ status }}

## Executive Summary

{{ executive_summary | default(value="Brief overview of the decision and its impact") }}

## Background

{{ background | default(value="Context and history leading to this decision") }}

## Problem Statement

{{ problem | default(value="The business problem being addressed") }}

## Proposed Solution

{{ solution | default(value="Recommended approach") }}

## Alternatives Considered

{% for alt in alternatives | default(value=[]) %}
### {{ alt.name }}
{{ alt.description }}
{% else %}
### Alternative 1
Description of alternative approach
{% endfor %}

## Cost-Benefit Analysis

### Costs
{% for cost in costs | default(value=[]) %}
* {{ cost }}
{% else %}
* Implementation cost
* Maintenance cost
{% endfor %}

### Benefits
{% for benefit in benefits | default(value=[]) %}
* {{ benefit }}
{% else %}
* Benefit 1
* Benefit 2
{% endfor %}

## Risk Assessment

{% for risk in risks | default(value=[]) %}
* {{ risk }}
{% else %}
* Risk 1: Mitigation strategy
{% endfor %}

## Implementation Plan

{{ implementation | default(value="High-level implementation approach") }}

## Success Metrics

{% for metric in metrics | default(value=[]) %}
* {{ metric }}
{% else %}
* Metric 1
{% endfor %}
"#;

/// Template engine for ADR generation.
#[derive(Debug)]
pub struct TemplateEngine {
    tera: Tera,
}

impl Default for TemplateEngine {
    fn default() -> Self {
        Self::new()
    }
}

impl TemplateEngine {
    /// Create a new template engine with built-in templates.
    #[must_use]
    pub fn new() -> Self {
        let mut tera = Tera::default();

        // Add built-in templates
        let _ = tera.add_raw_template("nygard", TEMPLATE_NYGARD);
        let _ = tera.add_raw_template("madr", TEMPLATE_MADR);
        let _ = tera.add_raw_template("y-statement", TEMPLATE_Y_STATEMENT);
        let _ = tera.add_raw_template("alexandrian", TEMPLATE_ALEXANDRIAN);
        let _ = tera.add_raw_template("business-case", TEMPLATE_BUSINESS_CASE);

        Self { tera }
    }

    /// Add a custom template.
    ///
    /// # Errors
    ///
    /// Returns an error if the template is invalid.
    pub fn add_template(&mut self, name: &str, content: &str) -> Result<(), Error> {
        self.tera
            .add_raw_template(name, content)
            .map_err(|e| Error::TemplateError {
                message: format!("Failed to add template '{name}': {e}"),
            })
    }

    /// Render a template with the given context.
    ///
    /// # Errors
    ///
    /// Returns an error if rendering fails.
    pub fn render(
        &self,
        template: &str,
        context: &HashMap<String, String>,
    ) -> Result<String, Error> {
        let mut tera_context = Context::new();
        for (key, value) in context {
            tera_context.insert(key, value);
        }

        self.tera
            .render(template, &tera_context)
            .map_err(|e| Error::TemplateError {
                message: format!("Failed to render template '{template}': {e}"),
            })
    }

    /// List available templates.
    #[must_use]
    pub fn list_templates(&self) -> Vec<String> {
        self.tera.get_template_names().map(String::from).collect()
    }

    /// Check if a template exists.
    #[must_use]
    pub fn has_template(&self, name: &str) -> bool {
        self.tera.get_template_names().any(|n| n == name)
    }

    /// Get template content.
    ///
    /// # Errors
    ///
    /// Returns an error if the template doesn't exist.
    pub fn get_template(&self, name: &str) -> Result<String, Error> {
        // Built-in templates
        match name {
            "nygard" => Ok(TEMPLATE_NYGARD.to_string()),
            "madr" => Ok(TEMPLATE_MADR.to_string()),
            "y-statement" => Ok(TEMPLATE_Y_STATEMENT.to_string()),
            "alexandrian" => Ok(TEMPLATE_ALEXANDRIAN.to_string()),
            "business-case" => Ok(TEMPLATE_BUSINESS_CASE.to_string()),
            _ => Err(Error::TemplateNotFound {
                name: name.to_string(),
            }),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_template_engine_new() {
        let engine = TemplateEngine::new();
        assert!(engine.has_template("nygard"));
        assert!(engine.has_template("madr"));
        assert!(!engine.has_template("nonexistent"));
    }

    #[test]
    fn test_template_engine_default() {
        let engine = TemplateEngine::default();
        assert!(engine.has_template("nygard"));
    }

    #[test]
    fn test_render_nygard() {
        let engine = TemplateEngine::new();
        let mut context = HashMap::new();
        context.insert("title".to_string(), "Test ADR".to_string());
        context.insert("status".to_string(), "Proposed".to_string());

        let result = engine
            .render("nygard", &context)
            .expect("Template should render successfully");
        assert!(result.contains("# Test ADR"));
        assert!(result.contains("## Status"));
        assert!(result.contains("Proposed"));
    }

    #[test]
    fn test_render_madr() {
        let engine = TemplateEngine::new();
        let mut context = HashMap::new();
        context.insert("title".to_string(), "MADR Test".to_string());
        context.insert("status".to_string(), "accepted".to_string());

        let result = engine.render("madr", &context).expect("Should render");
        assert!(result.contains("# MADR Test"));
        assert!(result.contains("Context and Problem Statement"));
    }

    #[test]
    fn test_render_y_statement() {
        let engine = TemplateEngine::new();
        let mut context = HashMap::new();
        context.insert("title".to_string(), "Y Statement Test".to_string());
        context.insert("status".to_string(), "proposed".to_string());

        let result = engine
            .render("y-statement", &context)
            .expect("Should render");
        assert!(result.contains("# Y Statement Test"));
        assert!(result.contains("In the context of"));
    }

    #[test]
    fn test_render_alexandrian() {
        let engine = TemplateEngine::new();
        let mut context = HashMap::new();
        context.insert("title".to_string(), "Alexandrian Test".to_string());
        context.insert("status".to_string(), "proposed".to_string());

        let result = engine
            .render("alexandrian", &context)
            .expect("Should render");
        assert!(result.contains("# Alexandrian Test"));
        assert!(result.contains("Prologue"));
        assert!(result.contains("Forces"));
    }

    #[test]
    fn test_render_business_case() {
        let engine = TemplateEngine::new();
        let mut context = HashMap::new();
        context.insert("title".to_string(), "Business Case Test".to_string());
        context.insert("status".to_string(), "proposed".to_string());

        let result = engine
            .render("business-case", &context)
            .expect("Should render");
        assert!(result.contains("# Business Case Test"));
        assert!(result.contains("Executive Summary"));
        assert!(result.contains("Cost-Benefit Analysis"));
    }

    #[test]
    fn test_list_templates() {
        let engine = TemplateEngine::new();
        let templates = engine.list_templates();
        assert!(templates.contains(&"nygard".to_string()));
        assert!(templates.contains(&"madr".to_string()));
        assert!(templates.contains(&"y-statement".to_string()));
        assert!(templates.contains(&"alexandrian".to_string()));
        assert!(templates.contains(&"business-case".to_string()));
    }

    #[test]
    fn test_add_custom_template() {
        let mut engine = TemplateEngine::new();
        let custom = "# {{ title }}\n\nCustom template content";
        engine
            .add_template("custom", custom)
            .expect("Should add template");
        assert!(engine.has_template("custom"));
    }

    #[test]
    fn test_get_template() {
        let engine = TemplateEngine::new();
        let nygard = engine.get_template("nygard").expect("Should get template");
        assert!(nygard.contains("## Context"));
    }

    #[test]
    fn test_get_template_not_found() {
        let engine = TemplateEngine::new();
        let result = engine.get_template("nonexistent");
        assert!(result.is_err());
    }

    #[test]
    fn test_render_nonexistent_template() {
        let engine = TemplateEngine::new();
        let context = HashMap::new();
        let result = engine.render("nonexistent", &context);
        assert!(result.is_err());
    }

    #[test]
    fn test_add_template_invalid() {
        let mut engine = TemplateEngine::new();
        // Invalid Tera template syntax
        let invalid = "{% for item in items %}{{ item }}{% endwith %}";
        let result = engine.add_template("invalid", invalid);
        assert!(result.is_err());
    }
}
