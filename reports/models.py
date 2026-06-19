from django.db import models
from django.utils import timezone

class Report(models.Model):
    SEX_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    lab_id = models.CharField(max_length=50, verbose_name="Lab ID -S-", blank=True, null=True)
    sample_type = models.CharField(max_length=50, default="BLOOD", blank=True, null=True)
    patient_name = models.CharField(max_length=150, blank=True, null=True)
    receiving_date = models.DateField(default=timezone.now, blank=True, null=True)
    reporting_date = models.DateField(default=timezone.now, blank=True, null=True)
    
    age_value = models.IntegerField(default=0, blank=True, null=True)
    age_unit = models.CharField(max_length=10, choices=[('Y', 'Years'), ('M', 'Months'), ('D', 'Days')], default='Y', blank=True, null=True)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, default='F', blank=True, null=True)
    ref_by = models.CharField(max_length=150, default="", blank=True, null=True)
    test_method = models.CharField(max_length=100, default="ELISA", blank=True, null=True)
    
    # Bottom Note
    notes = models.TextField(
        default="This report is not valid for any medico-legal purpose. Result reflect to the sample as received. Interpretation can be done by Clinician. Please contact the Lab for any clarification/re-evalutation of the result."
    )
    
    # Signature configurations
    show_prepared_by = models.BooleanField(default=True)
    show_technician = models.BooleanField(default=True)
    show_scientist = models.BooleanField(default=True)
    show_vc = models.BooleanField(default=True)
    
    prepared_by_name = models.CharField(max_length=100, default="Report Prepared by")
    technician_name = models.CharField(max_length=100, default="Lab Technician / RA")
    scientist_name = models.CharField(max_length=100, default="Research Scientist")
    vc_name = models.CharField(max_length=100, default="Dr. G.C Sahoo")
    vc_title = models.CharField(max_length=100, default="Signature of VC")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.lab_id} - {self.patient_name}"

    class Meta:
        ordering = ['-created_at']


class ReportTest(models.Model):
    TEST_CHOICES = [
        ('Anti-HBc IgM', 'Anti-HBc IgM'),
        ('Anti-HBc Total', 'Anti-HBc Total'),
        ('Anti-HBe', 'Anti-HBe'),
        ('Anti-HBs', 'Anti-HBs'),
        ('Calicivirus','Calicivirus'  ),
        ('Chikungunya', 'Chikungunya'),
        ('Chikungunya IgG', 'Chikungunya IgG'),
        ('Chikungunya IgM', 'Chikungunya IgM'),
        ('Dengue', 'Dengue'),
        ('Dengue IgG', 'Dengue IgG'),
        ('Dengue IgM', 'Dengue IgM'),
        ('Dengue NS1', 'Dengue NS1'),
        ('HAV IgG', 'HAV IgG'),
        ('HAV IgM', 'HAV IgM'),
        ('HBeAg', 'HBeAg'),
        ('HBsAg', 'HBsAg'),
        ('HBV DNA', 'HBV DNA'),
        ('HCV Antibody', 'HCV Antibody'),
        ('HCV RNA','HCV RNA' ),
        ('HEV IgG', 'HEV IgG'),
        ('HEV IgM', 'HEV IgM'),
        ('Influenza H1N1', 'Influenza H1N1'),
        ('Influenza H3N2', 'Influenza H3N2'),
        ('JE IgM (Blood)', 'JE IgM (Blood)'),
        ('JE IgM (CSF)', 'JE IgM (CSF)'),
        ('Leptospira', 'Leptospira'),
        ('Leptospira IgM', 'Leptospira IgM'),
        ('Leptospira', 'Leptospira'),
        ('Measles', 'Measles'),
        ('Measles IgG', 'Measles IgG'),
        ('Measles IgM', 'Measles IgM'),
        ('Mumps', 'Mumps'),
        ('Mumps IgG', 'Mumps IgG'),
        ('Mumps IgM', 'Mumps IgM'),
        ('Scrub Typhus (ST)', 'Scrub Typhus (ST)'),
        ('Scrub Typhus IgM', 'Scrub Typhus IgM'),
        ('VZV IgG', 'VZV IgG'),
        ('VZV IgM', 'VZV IgM'),
        ('Zika Virus IgM', 'Zika Virus IgM'),
        ('Zika Virus RNA', 'Zika Virus RNA'),
        ('Influenza VICTORIA', 'Influenza VICTORIA'),
    ]
    report = models.ForeignKey(Report, related_name='tests', on_delete=models.CASCADE)
    test_name = models.CharField(max_length=100, db_index=True)
    result_value = models.CharField(max_length=50, blank=True, null=True)
    interpretation_text = models.CharField(max_length=50, blank=True, null=True, db_index=True)

    def save(self, *args, **kwargs):
        method = (self.report.test_method or '').upper()
        if method == 'ELISA':
            if self.result_value:
                try:
                    val = float(self.result_value)
                    if val < 9.0:
                        self.interpretation_text = "Negative"
                    elif val > 11.0:
                        self.interpretation_text = "Positive"
                    else:
                        self.interpretation_text = "Equivocal"
                except ValueError:
                    # Keep interpretation if provided manually or clear it
                    pass
        elif method in ['RT-PCR', 'RAPID'] or method:
            # If they enter 'Positive' or 'Negative' directly in result
            val = str(self.result_value).strip().lower()
            if val in ['positive', 'negative', 'equivocal', 'invalid']:
                self.interpretation_text = val.capitalize()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.test_name}: {self.result_value} ({self.interpretation_text})"
