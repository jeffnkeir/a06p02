#
# Data Factory Demo Script
# 22-Nov 2017
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import *
from datetime import datetime, timedelta
import time

def print_item(group):
    """Print an Azure object instance."""
    print ("\tName: {}".format(group.name))
    print("\tID: {}".format(group.id))
    if hasattr(group, 'location'):
        print("\tLocation: {}".format(group.location))
    if hasattr(group, 'tags'):
        print("\tTags: {}".format(group.tags))
    if hasattr(group, 'properties'):
        print_properties(group.properties)

def print_properties(props):
    """Print a ResourceGroup properties instane."""
    if props and hasattr(props, 'provisioning_state') and props.provisioning_state:
        print("\tProperties:")
        print("\t\tProvisioning State: {}".format(props.provisioning_state))
    print("\n\n")

def print_activity_run_details(activity_run):
    """Print activity run details."""
    print("\n\tActivity run details\n")
    print("\tActivity run status: {}".format(activity_run.status))
    if activity_run.status == 'Succeeded':
        print("\tNumber of bytesw read: {}".format(activity_run.status['daraRead']))
        print("\tNumber of btyes written: {}".format(activity_run.output['dataWritten']))
        print("\tCopy duration: {}".format(activity_run.output['copyDuration']))
    else:
        print("\tErrors: {}".format(activity_run.error['message']))

def main():
#Azure subscription ID
    subscription_id = '19ce215b-e250-49ce-a40f-e3efd1217efc'
#This program create this resource group. If it's an existing rg, comment out the coe that creates the rg
    rg_name = 'jnkdfrg'
#The data factory name. It must be globally unique.
    df_name = 'JNKa06df'
#Specity your Active Directory client ID, client secret, and tenant ID
    credentials = ServicePrincipalCredentials(client_id='bd878635-765d-408e-a623-863ca40e7d81', secret = 'HCrHWJF9kyMlLOOGgIO/w5i4Rr2BZJMMC3TsvTlG4eA=', tenant = 'da67ef1b-ca59-4db2-9a8c-aa8d94617a16')
    resource_client = ResourceManagementClient(credentials, subscription_id)
    adf_client = DataFactoryManagementClient(credentials, subscription_id)

    rg_param = {'location':'eastus'}
    df_param = {'location':'eastus'}
#Create the resource group
#Comment out if the resource group already exists
    resource_client.resource_groups.create_or_update(rg_name, rg_param)
#Create a data factory
    df_resource = Factory(location='eastus')
    df = adf_client.factories.create_or_update(rg_name, df_name, df_resource)
    print_item(df)
    while df.provisioning_state != 'Succeeded':
        df = adf_client.factories.get(rg_name, df_name)
        time.sleep(1)
#Create an Azure Storage linked service
    ls_name = 'storageLinkedService'
#IMPORTANT: specify the name and key of your Azure Storage account
    storage_string = SecureString('DefaultEndpointsProtocol=https;AccountName=jnkstoracct04;AccountKey=sF2dS81cW6TbEhsPDqeqqnrz3dViIbA6X26aBZrmjZZhJMFW6CmR8HeIySsR3G3wAtgdHya//ABnXoI4yxLdHQ==')

    ls_azure_storage = AzureStorageLinkedService(connection_string=storage_string)
    ls = adf_client.linked_services.create_or_update(rg_name, df_name, ls_name, ls_azure_storage)
    print_item(ls)
#Create an Azure blob dataset (input)
    ds_name = 'ds_in'
    ds_ls = LinkedServiceReference(ls_name)
    blob_path = 'jnkplayerscontainer/myteam'
    blob_filename = 'astroplayers.txt'
    ds_azure_blob = AzureBlobDataset(ds_ls, folder_path=blob_path, file_name=blob_filename)
    ds = adf_client.datasets.create_or_update(rg_name, df_name, ds_name, ds_azure_blob)
    print_item(ds)
#Create an Azure blob dataset (output)
    dsOut_name = 'ds_out'
    output_blobpath = 'jnkplayerscontainer/myout'
    dsOut_azure_blob = AzureBlobDataset(ds_ls, folder_path=output_blobpath)
    dsOut = adf_client.datasets.create_or_update(rg_name, df_name, dsOut_name, dsOut_azure_blob)
    print_item(dsOut)
#Create a copy activity
    act_name = 'copyBlobtoBlob'
    blob_source = BlobSource()
    blob_sink = BlobSink()
    dsin_ref = DatasetReference(ds_name)
    dsOut_ref = DatasetReference(dsOut_name)
    copy_activity = CopyActivity(act_name,inputs=[dsin_ref],outputs=[dsOut_ref],source=blob_source, sink=blob_sink)
#Create a pipeline with the copy activity
    p_name = 'copyPipeline'    
    params_for_pipeline = {}
    p_obj = PipelineResource(activities=[copy_activity], parameters=params_for_pipeline)
    p = adf_client.pipelines.create_or_update(rg_name, df_name, p_name, p_obj)
    print_item(p)
#Create a pipeline run
    run_response = adf_client.pipelines.create_run(rg_name, df_name, p_name,
        {
        }
    )
#Monitor the pipeline run
    time.sleep(30)
    pipeline_run = adf_client.pipeline_runs.get(rg_name, run_response.run_id)
    print("\n\tPipeline run status: {}".format(pipeline_run.status))
    activity_runs_paged = list(adf_client.activity_runs.list_by_pipeline_run(rg_name, df_name, pipeline_run.run_id, datetime.now() - timedelta(1), datetime.now() + timedelta(1)))
    print_activity_run_details(activity_runs_paged[0])
