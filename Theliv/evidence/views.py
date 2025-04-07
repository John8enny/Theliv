from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Evidence
from .forms import EvidenceForm
from .forms import TransferForm
from django.utils.timezone import now
import hashlib
import json
from django.http import JsonResponse
#from accounts.models import CustomUser
from django.contrib.auth.models import User, Group
from api.ipfs_utils import upload_to_ipfs
from django.db.models import Q
from .forms import SearchForm
import requests
from django.conf import settings
import os
import re
import datetime
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from tika import parser
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
import io

FABLO_API_URL = "http://localhost:3000/evidence/add"

def generate_evidence_id(case_num):
    timestamp = now().strftime('%Y%m%d%H%M%S')
    return f"{case_num}_{timestamp}"

def calculate_file_hash(file):
    sha256 = hashlib.sha256()
    for chunk in file.chunks():
        sha256.update(chunk)
    return sha256.hexdigest()

@login_required
def dashboard(request):
    # Get evidences assigned to the current user
    user_evidences = Evidence.objects.filter(added_by_django=request.user.username)
    evidence_count = user_evidences.count()

    # Bar Chart: Evidence by File Type
    file_type_counts = user_evidences.values('file_type').annotate(count=Count('id')).order_by('file_type')
    file_types = [item['file_type'] for item in file_type_counts] or ['No Data']
    file_type_data = [item['count'] for item in file_type_counts] or [0]
    print("File Types:", file_types)  # Debug output
    print("File Type Counts:", file_type_data)

    # Line Chart: Evidence Over Time (last 30 days)
    today = timezone.now().date()
    thirty_days_ago = today - datetime.timedelta(days=30)
    time_data = user_evidences.filter(timestamp__gte=thirty_days_ago).annotate(
        day=TruncDate('timestamp')
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    dates = [item['day'].strftime('%Y-%m-%d') if item['day'] else 'No Date' for item in time_data] or [thirty_days_ago.strftime('%Y-%m-%d')]
    counts = [item['count'] for item in time_data] or [0]
    print("Dates:", dates)  # Debug output
    print("Counts:", counts)

    return render(request, 'evidence/dashboard.html', {
        'username': request.user.username,
        'evidence_count': evidence_count,
        'user_evidences': user_evidences,
        'file_types': file_types,
        'file_type_data': file_type_data,
        'dates': dates,
        'counts': counts,
    })

@login_required
def submit_evidence(request):
    if request.method == 'POST':
        form = EvidenceForm(request.POST, request.FILES)
        if form.is_valid():
            case_num = form.cleaned_data['case_num']
            evd_name = form.cleaned_data['evd_name']
            file = form.cleaned_data['file']

            # Retrieve dynamically added custom fields and convert to JSON
            custom_fields = {}
            for key, value in request.POST.items():
                if key.startswith('custom_field_name_'):
                    field_index = key.split('_')[-1]
                    field_name = value
                    field_value = request.POST.get(f'custom_field_value_{field_index}')
                    if field_name and field_value:
                        custom_fields[field_name] = field_value

             # Upload the file to IPFS and get CID
            cid = upload_to_ipfs(file)
            print(f"Successfully uploaded to IPFS. CID: {cid}")
            file.seek(0)

            # Save evidence with CID
            #evidence = form.save(commit=False)
            #evidence.cid = cid
            #evidence.save()

            # Generate Evidence ID
            evd_id = generate_evidence_id(case_num)

            # Calculate File Hash
            file_hash = calculate_file_hash(file)
            file.seek(0)

            # *** Change: Use Tika to extract metadata ***
            # Save file temporarily to disk for Tika parsing
            temp_file_path = default_storage.save(f'tmp/{file.name}', ContentFile(file.read()))
            full_temp_path = os.path.join(settings.MEDIA_ROOT, temp_file_path)
            try:
                parsed = parser.from_file(full_temp_path, 'http://localhost:9998/tika')
                metadata = parsed.get('metadata', {})
                # Ensure metadata is a dict and filter out unwanted keys if needed
                if not isinstance(metadata, dict):
                    metadata = {}
                for key, value in metadata.items():
                    if isinstance(value, (list, tuple)):
                         metadata[key] = ', '.join(str(v) for v in value)  # Join arrays into a single string
                    else:
                         metadata[key] = str(value)  # Ensure everything is a string
                metadata.update({
                    'file_size': str(file.size),
                    'uploaded_at': str(now())
                })

            except Exception as e:
                print(f"Tika extraction failed: {str(e)}")
                # Fallback to basic metadata if Tika fails
                metadata = {
                    'file_name': file.name,
                    'file_size': str(file.size),
                    'uploaded_at': str(now())
                }
            finally:
                # Clean up temporary file
                if os.path.exists(full_temp_path):
                    os.remove(full_temp_path)

            # Save evidence to database
            evidence = form.save(commit=False)
            evidence.id = evd_id
            evidence.cid = cid
            evidence.file_hash = file_hash
            evidence.metadata = metadata
            evidence.custom_data = custom_fields
            evidence.added_by_django = request.user.username
            evidence.timestamp = now()
            evidence.save()

            # Convert custom fields (custom_data) to JSON string
            custom_data_str = json.dumps(custom_fields)

            #if serialized json is needed
            metadata_str = json.dumps(metadata) 


            # Prepare data for Fablo API
            fablo_data = {
                "id": evd_id,                  # ID
                "cid": cid,                    # CID
                "fileHash": file_hash,         # FileHash
                "evdName": evd_name,           # EvdName
                "caseNum": case_num,           # CaseNum
                "description": form.cleaned_data.get('description', ''),  # Description (assuming from form)
                "fileType": form.cleaned_data['file_type'],  # FileType
                "metadata": metadata_str,          # Metadata (as dict, not string)
                "customData": custom_data_str,   # CustomData (as dict)
                "addedByDjango": request.user.username  # AddedByDjango
            }

            print("Payload being sent to Fablo API:")
            print(json.dumps(fablo_data, indent=4))

            # Send data to Fablo API
            try:
                response = requests.post(
                    FABLO_API_URL,
                    json=fablo_data,
                    headers={'Content-Type': 'application/json'}
                )

                if response.status_code == 200:
                    messages.success(request, "Evidence submitted successfully and added to Fablo!")
                    return redirect('preview_evidence', evd_id=evd_id)
                else:
                    messages.error(request, f"Failed to submit to Fablo. Error: {response.text}")
                    return redirect('submit_evidence')

            except requests.RequestException as e:
                messages.error(request, f"Error connecting to Fablo API: {str(e)}")
                evidence.delete()
                return redirect('submit_evidence')
    else:
        form = EvidenceForm()

    return render(request, 'evidence/submit_evidence.html', {
        'form': form
    })
    pass

@login_required
def preview_evidence(request, evd_id):
    evidence = get_object_or_404(Evidence, id=evd_id)

    # Check access permissions
    is_owner = evidence.added_by_django == request.user.username
    is_superuser = request.user.is_superuser
    is_admin = request.user.groups.filter(name='admin').exists()

    if not (is_owner or is_superuser or is_admin):
        messages.error(request, "You do not have permission to preview this evidence.")
        return redirect('view_evidence')  # Redirect to a safe page

    # Detect file type for preview
    file_type = evidence.file_type.lower()
    preview_supported = file_type in ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi', 'mkv', 'mp3', 'wav', 'pdf', 'txt']

        # Handle PDF export
    if 'export_pdf' in request.GET:
        # Create a PDF response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="evidence_{evd_id}.pdf"'

        # Buffer to hold PDF data
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=20, bottomMargin=20)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        elements.append(Paragraph("Evidence Details", styles['Title']))
        elements.append(Spacer(1, 20))

        # Evidence details as a table
        data = [
            ["Field", "Value"],
            ["Evidence ID", evidence.id],
            ["CID (IPFS)", evidence.cid],
            ["File Hash", evidence.file_hash],
            ["Evidence Name", evidence.evd_name],
            ["Case Number", evidence.case_num],
            ["Description", evidence.description or "N/A"],
            ["File Type", evidence.file_type],
            ["Submitted By", evidence.added_by_django],
            ["Timestamp", str(evidence.timestamp)],
        ]
        evidence_table = Table(data, colWidths=[150, 350])
        evidence_table.setStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        elements.append(evidence_table)
        elements.append(Spacer(1, 20))  # Space before next section

        # Metadata
        elements.append(Paragraph("Metadata", styles['Heading2']))
        elements.append(Spacer(1, 12))
        metadata_data = [["Key", "Value"]] + [[k, str(v)] for k, v in evidence.metadata.items()]
        metadata_table = Table(metadata_data, colWidths=[150, 350])
        metadata_table.setStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        elements.append(metadata_table)
        elements.append(Spacer(1, 20))  # Space before next section

        # Custom Data
        if evidence.custom_data:
            elements.append(Paragraph("Custom Data", styles['Heading2']))
            elements.append(Spacer(1, 12))
            custom_data_str = json.dumps(evidence.custom_data, indent=2)
            elements.append(Paragraph(custom_data_str, styles['Normal']))

        # Build PDF
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        return response

    return render(request, 'evidence/preview_evidence.html', {
        'evidence': evidence,
        'preview_supported': preview_supported,
        'file_type': file_type,
    })
def view_evidence(request):
    form = SearchForm(request.GET)
    evidence_list = None
    single_evidence = None

    if form.is_valid():
        evidence_number = form.cleaned_data.get('evidence_number')
        case_number = form.cleaned_data.get('case_number')

        if evidence_number:
            try:
                single_evidence = Evidence.objects.get(id=evidence_number)
            except Evidence.DoesNotExist:
                messages.error(request, "No evidence found with this Evidence Number.")

        elif case_number:
            evidence_list = Evidence.objects.filter(case_num=case_number)
            if not evidence_list.exists():
                messages.error(request, "No evidence found for this Case Number.")

    return render(request, 'evidence/view_evidence.html', {
        'form': form,
        'evidence_list': evidence_list,
        'single_evidence': single_evidence,
    })
#if something breaks comment from here onwards

# views.py
@login_required
def transfer_evidence(request):
    FABLO_TRANSFER_API_URL = "http://localhost:3000/evidence/transfer"
    form = TransferForm(request.POST or request.GET)
    evidence_list = None
    single_evidence = None
    selected_evidence_ids = request.POST.getlist('selected_evidence') if request.method == 'POST' else []

    if form.is_valid():
        evidence_number = form.cleaned_data.get('evidence_number')
        case_number = form.cleaned_data.get('case_number')
        recipient = form.cleaned_data.get('recipient')

        # Check user permissions
        is_superuser = request.user.is_superuser
        is_admin = request.user.groups.filter(name='admin').exists()

        # Handle search first
        if request.method == 'GET' or (request.method == 'POST' and not selected_evidence_ids):
            if evidence_number:
                try:
                    single_evidence = Evidence.objects.get(id=evidence_number)
                except Evidence.DoesNotExist:
                    messages.error(request, "No evidence found with this Evidence Number.")
            
            elif case_number:
                evidence_list = Evidence.objects.filter(case_num=case_number)
                if not evidence_list.exists():
                    messages.error(request, "No evidence found for this Case Number.")

        # Handle transfer submission
        if request.method == 'POST' and selected_evidence_ids and recipient:
            try:
                evidences_to_transfer = Evidence.objects.filter(id__in=selected_evidence_ids)
                successful_transfers = 0

                for evidence in evidences_to_transfer:

                    # Check if user is owner, superuser, or in admin group
                    is_owner = evidence.added_by_django == request.user.username
                    if not (is_owner or is_superuser or is_admin):
                        messages.error(request, f"You do not have permission to transfer evidence {evidence.id}.")
                        continue  # Skip to next evidence

                    # Prepare data for Fabric Transfer API
                    transfer_data = {
                        "evidenceId": evidence.id,
                        "newOwnerDjango": recipient.username
                    }

                    # Send to Fabric Transfer API
                    response = requests.post(
                        FABLO_TRANSFER_API_URL,
                        json=transfer_data,
                        headers={'Content-Type': 'application/json'}
                    )

                    if response.status_code == 200:
                        # Update local database only if Fabric transfer succeeds
                        evidence.added_by_django = recipient.username
                        evidence.save()
                        successful_transfers += 1
                    else:
                        messages.error(request, f"Failed to transfer evidence {evidence.id} to Fabric: {response.text}")

                if successful_transfers > 0:
                    messages.success(request, f"Successfully transferred {successful_transfers} evidence item(s) to {recipient.username}")
                if successful_transfers < len(evidences_to_transfer):
                    messages.warning(request, f"{len(evidences_to_transfer) - successful_transfers} evidence item(s) failed to transfer")
                
                return redirect('transfer_evidence')
            
            except requests.RequestException as e:
                messages.error(request, f"Error connecting to Fabric Transfer API: {str(e)}")
            except Exception as e:
                messages.error(request, f"Error during transfer: {str(e)}")

    return render(request, 'evidence/transfer_evidence.html', {
        'form': form,
        'evidence_list': evidence_list,
        'single_evidence': single_evidence,
        'selected_evidence_ids': selected_evidence_ids,
    })

FABLO_GET_HISTORY_API_URL = "http://localhost:3000/evidence/history/"

@login_required
def audit_evidence(request):
    
    # Check access permissions
    is_superuser = request.user.is_superuser
    is_admin = request.user.groups.filter(name='admin').exists()
    is_judiciary = request.user.groups.filter(name='judiciary').exists()

    if not (is_superuser or is_admin or is_judiciary):
        messages.error(request, "You do not have permission to audit evidence.")
        return redirect('dashboard')  # Redirect to a safe page
    
    form = SearchForm(request.GET or None)
    history_data = None
    error_message = None

    if request.method == 'GET' and form.is_valid():
        evidence_number = form.cleaned_data.get('evidence_number')
        if evidence_number:
            try:
                response = requests.get(
                    f"{FABLO_GET_HISTORY_API_URL}{evidence_number}",
                    headers={'Content-Type': 'application/json'}
                )
                if response.status_code == 200:
                    response_json = response.json()
                    result_text = response_json.get('result', '')
                    payload_start = result_text.find('payload:"')
                    if payload_start != -1:
                        payload_start += len('payload:"')
                        payload_end = result_text.rfind('"', payload_start)
                        if payload_end != -1:
                            payload_str = result_text[payload_start:payload_end].replace('\\"', '"')
                            try:
                                history_data = json.loads(payload_str)
                                # Preprocess timestamps
                                for event in history_data:
                                    seconds_match = re.search(r'seconds:(\d+)', event['timestamp'])
                                    if seconds_match:
                                        seconds = int(seconds_match.group(1))
                                        event['formatted_timestamp'] = datetime.datetime.fromtimestamp(
                                            seconds, tz=datetime.timezone.utc
                                        ).strftime('%Y-%m-%d %H:%M:%S')
                                    else:
                                        event['formatted_timestamp'] = "Invalid timestamp"
                            except json.JSONDecodeError as e:
                                error_message = f"Failed to parse payload JSON: {str(e)}"
                        else:
                            error_message = "Could not find payload end in API response"
                    else:
                        error_message = "Could not find payload in API response"
                else:
                    error_message = f"Failed to retrieve evidence history: {response.text}"
            except requests.RequestException as e:
                error_message = f"Error connecting to Fabric API: {str(e)}"
            except (json.JSONDecodeError, ValueError) as e:
                error_message = f"Invalid JSON format in API response: {str(e)}"

    return render(request, 'evidence/audit_evidence.html', {
        'form': form,
        'history_data': history_data,
        'error_message': error_message,
    })
