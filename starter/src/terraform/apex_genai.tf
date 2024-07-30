#-- IDCS_URL ----------------------------------------------------------

variable idcs_domain_name { default = "Default" }
variable idcs_url { default = "" }

data "oci_identity_domains" "starter_domains" {
    #Required
    compartment_id = var.tenancy_ocid
    display_name = var.idcs_domain_name
}

locals {
  idcs_url = (var.idcs_url!="")?var.idcs_url:data.oci_identity_domains.starter_domains.domains[0].url
}

#-- Object Storage ----------------------------------------------------------

# Object Storage
variable "namespace" {}

resource "oci_objectstorage_bucket" "starter_bucket" {
  compartment_id = local.lz_security_cmp_ocid
  namespace      = var.namespace
  name           = "${var.prefix}-public-bucket"
  access_type    = "ObjectReadWithoutList"
  object_events_enabled = true

  freeform_tags = local.freeform_tags
}

locals {
  bucket_url = "https://objectstorage.${var.region}.oraclecloud.com/n/${var.namespace}/b/${var.prefix}-public-bucket/o"
}  

resource "oci_identity_domains_dynamic_resource_group" "starter-adb-dyngroup" {
    #Required
    provider       = oci.home    
    display_name = "${var.prefix}-adb-dyngroup"
    idcs_endpoint = local.idcs_url
    matching_rule = "ANY{ resource.id = '${oci_database_autonomous_database.starter_atp.id}' }"
    schemas = ["urn:ietf:params:scim:schemas:oracle:idcs:DynamicResourceGroup"]
}

resource "oci_identity_domains_dynamic_resource_group" "starter-instance-dyngroup" {
    #Required
    provider       = oci.home    
    display_name = "${var.prefix}-instance-dyngroup"
    idcs_endpoint = local.idcs_url
    matching_rule = "ANY{ instance.compartment.id = '${local.lz_appdev_cmp_ocid}' }"
    schemas = ["urn:ietf:params:scim:schemas:oracle:idcs:DynamicResourceGroup"]
}

resource "time_sleep" "wait_30_seconds" {
  depends_on = [ oci_identity_domains_dynamic_resource_group.starter-adb-dyngroup, oci_identity_domains_dynamic_resource_group.starter-instance-dyngroup ]
  create_duration = "30s"
}

resource "oci_identity_policy" "starter-adb-policy" {
    provider       = oci.home    
    depends_on     = [ time_sleep.wait_30_seconds ]
    name           = "${var.prefix}-adb-policy"
    description    = "${var.prefix} adb policy"
    compartment_id = local.lz_appdev_cmp_ocid

    statements = [
        "Allow dynamic-group ${var.prefix}-adb-dyngroup to manage generative-ai-family in compartment id ${var.compartment_ocid}"
    ]
}

resource "oci_identity_policy" "starter-instance-policy" {
    provider       = oci.home    
    depends_on     = [ time_sleep.wait_30_seconds ]
    name           = "${var.prefix}-instance-policy"
    description    = "${var.prefix} instance policy"
    compartment_id = local.lz_appdev_cmp_ocid

    statements = [
        "Allow dynamic-group ${var.prefix}-instance-dyngroup to manage generative-ai-family in compartment id ${var.compartment_ocid}"
    ]
}
