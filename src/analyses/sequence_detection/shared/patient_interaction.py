from src.core.io.file_utils import FileUtils

class PatientConverter:
    @classmethod
    def get_courses_from_patientes(cls, patients):
        courses = []
        for patient in patients:
            courses += patient.courses

        return courses

    @classmethod
    def get_provider_sequence_ids_from_course_list(cls, courses):
        provider_sequences = {}
        for i, course in enumerate(courses):
            for provider in course.involved_providers:
                l = provider_sequences.get(provider, [])
                l.append(i)
                provider_sequences[provider] = l

        return provider_sequences

    @classmethod
    def get_provider_courses(cls, courses: list) -> dict:
        provider_sequences = cls.get_provider_sequence_ids_from_course_list(courses)
        ret = {}
        for provider, sequence_idx in provider_sequences.items():
            course_data = [courses[x] for x in sequence_idx]
            ret[provider] = course_data

        return ret

    @classmethod
    def get_courses_by_context(cls, courses: list) -> dict:
        ret = {}
        for course in courses:
            context = course.context
            current = ret.get(context, [])
            current.append(course)
            ret[context] = current

        return ret