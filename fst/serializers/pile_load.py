from .base import BaseReportSerializer

class PileLoadSerializer(BaseReportSerializer):
    def __init__(self, record):
        self.record = record

    def serialize(self):
        rec = self.record

        return {
            # meta
            "report_type": rec._name,
            "report_no": rec.report_no,
            "ulr": rec.ulr,

            # project
            "project": rec.name,
            "work_name": rec.work_name,
            "client": rec.client.name if rec.client else "",
            "contractor": rec.contractor.partner_id.name if rec.contractor else "",
            "site_location": rec.site_location,
            "rec_date": rec.rec_date_str,
            "test_standard": rec.test_standard,

            # pile
            "pile_no": rec.pile_no,
            "diameter": rec.diameter,
            "dial_gauge_count": rec.dial_gauge_count,

            # test
            "test_load": rec.test_load,
            "incremental_load": rec.incremental_load,
            "allowable_capacity": rec.allowable_capacity,

            # report text
            "introduction": rec.introduction,
            "objective": rec.objective,
            "test_equipment": rec.test_equipment,
            "test_procedure": rec.test_procedure,
            "analysis_text": rec.analysis_text,
            "interpretation": rec.interpretation,
            "conclusion": rec.conclusion,

            # summary
            "gross_settlement": rec.gross_settlement,
            "net_settlement": rec.net_settlement,
            "rebound": rec.rebound,
            "max_settlement": rec.max_settlement,

            # signatory
            # "signatory_name": rec.signatory_name,
            # "signatory_designation": rec.signatory_designation,

            # images
            # "cover_image": rec.cover_image,
            "graph_image": rec.graph_image,
            "qr_code": rec.qr_code,

            # tables
            "basic_data": self._basic_data(rec.basic_data_ids),
            "contents": self._contents(rec.content_ids),
            "site_images": self._site_images(rec.site_image_ids),

            # observations
            "loading": self._reading_rows(rec.loading_reading_ids),
            "unloading": self._reading_rows(rec.unloading_reading_ids),
        }

    def _reading_rows(self, lines):
        rows = []

        for line in lines:
            row = {
                "date": line.reading_date_str,
                "time": line.reading_time_str,
                "load": line.load_tonne,
                "dial_a": line.dial_a,
                "dial_b": line.dial_b,
                "mean": line.mean_mm,
            }

            if hasattr(line, "dial_c"):
                row["dial_c"] = line.dial_c

            if hasattr(line, "dial_d"):
                row["dial_d"] = line.dial_d

            rows.append(row)

        return rows
    
    def _basic_data(self, lines):
        return [
            {
                "sr_no": l.sr_no,
                "parameter": l.parameter,
                "value": l.value,
            }
            for l in lines
        ]


    def _contents(self, lines):
        return [
            {
                "sequence": l.sequence,
                "description": l.description,
                "page_no": l.page_no,
            }
            for l in lines
        ]


    def _site_images(self, lines):
        return [
            {
                "name": l.sequence,
                "image": l.image,
            }
            for l in lines
        ]