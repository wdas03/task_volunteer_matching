from __future__ import annotations
from util import load_volunteers, load_tasks, get_volunteer_satisfaction_score
from task import Task
from volunteer import Volunteer

from heapq import heapify, heappop, heappush

class AssignmentServer:
    def __init__(self):
        self.assignments: dict[Volunteer, set[Task]] = {}
        self.tasks: dict[int, Task] = {}
        self.volunteers: list[Volunteer] = []

    def import_tasks_from_csv(self, csv_filename: str):
        self.tasks = load_tasks(csv_filename)

    def import_volunteers_from_csv(self, csv_filename: str):
        self.volunteers.extend(load_volunteers(csv_filename, self.tasks))

    def get_interested_volunteers(self, task: Task) -> list[Volunteer]:
        """
        Returns a List of the Volunteers who have indicated interest in the
        given task.
        """
        interested_volunteers = []
        for volunteer in self.volunteers:
            if task in volunteer.interested_tasks:
                interested_volunteers.append(volunteer)

        return interested_volunteers

    def _get_overall_task_desirability_score(self, task: Task) -> float:
        """
        Returns a float representing the overall task desirability score for a specific task.

        The overall task desirability score is the sum of the task desirability scores for each interested volunteer.
        """
        total_score = 0
        for volunteer in self.get_interested_volunteers(task):
            total_score += volunteer.get_task_desirability_score(task)
        
        return total_score

    def get_tasks_by_desirability(self) -> list[Task]:
        """
        Returns a List of Tasks sorted by desirability.
        """

        # TODO: Implement this method. See the README for more details.
        # Added _get_task_desirability_score function above to get overall task desirability for a specific task

        # Sort tasks by overall desirability score (highest to lowest)
        sorted_tasks = sorted(self.tasks.values(), key=lambda _task: self._get_overall_task_desirability_score(_task), reverse=True)

        # Move people-facing tasks to the front of the list
        people_facing_tasks = [_task for _task in sorted_tasks if _task.people_facing]
        non_people_facing_tasks = [_task for _task in sorted_tasks if not _task.people_facing]

        # Return final sorted list (people-facing tasks first, then non-people-facing tasks, both sorted by overall desirability score)
        return people_facing_tasks + non_people_facing_tasks

    def assign_tasks(self):
        """
        Assigns Tasks to Volunteers by inserting them into the assignment map,
        in order of desirability. Tasks are assigned to the first Volunteer with
        interest. If there are no interested Volunteers, they are assigned to the
        first available Volunteer.
        """
        for task in self.get_tasks_by_desirability():
            interested_volunteers = self.get_interested_volunteers(task)

            if len(interested_volunteers) > 0:
                self.assign_task(task, interested_volunteers[0])
            elif len(self.volunteers) > 0:
                self.assign_task(task, self.volunteers[0])

    def assign_task(self, task: Task, volunteer: Volunteer):
        """
        Adds the given Task to the specified Volunteer's Set of assigned Tasks.
        """
        if volunteer not in self.assignments:
            self.assignments[volunteer] = set()
        self.assignments[volunteer].add(task)

    def assign_tasks_improved(self):
        """
        Assigns Tasks to Volunteers based on their interests using a greedy algorithm.

        The assign_tasks_improved function aims to maximize volunteer satisfaction using min-heaps to optimize the assignment process.
        
        Initially, a min-heap is created with volunteers sorted by their current workload, allowing for quick identification of the least-burdened volunteer. 
        
        When tasks come up for assignment, two cases are considered:

        - If multiple volunteers are interested in a task, a new min-heap is generated for these interested volunteers. This heap sorts them based on both their current workload and their level of interest in the specific task.
        - If no volunteers are interested, the algorithm falls back to the original min-heap to find the least-burdened volunteer overall.

        In either case, after a task is assigned, the heap is updated to reflect the new workload, enabling ongoing efficient assignment. 

        Why It's More Optimal:
        - The use of heaps allows for O(log N) complexity when updating workloads, making the process efficient.
        - By considering both the desirability of tasks and the interests of volunteers, the algorithm aims to make more satisfying matches.
        - The sorting of tasks and volunteers based on multiple criteria ensures that the most favorable tasks get assigned to the most interested volunteers first, likely resulting in a higher overall satisfaction score.
        """

        # TODO: Implement this method. See the README for more details.

        try:
            # Clear existing assignments
            self.assignments.clear()

            # Initialize heap for volunteers based on their current workload (fewest tasks first)
            # Use arbitrary id of volunteer to break ties in case of equal workloads
            volunteer_heap = [(0, id(volunteer), volunteer) for volunteer in self.volunteers]
            heapify(volunteer_heap)

            for task in self.tasks.values():
                interested_volunteers = self.get_interested_volunteers(task)

                if interested_volunteers:
                    # Sort interested volunteers based on their ranking for the task
                    interested_volunteers.sort(key=lambda v: v.interested_tasks.index(task))

                    # Create heap for interested volunteers based on their current workload and ranking
                    # Use number of assignments volunteer has to first represent workload
                    # Then use the position of the task in the volunteer's interested_tasks list to represent ranking (lower index = higher ranking/interest)
                    # Use arbitrary id of volunteer to break ties in case of equal workloads and rankings
                    interested_heap = [(len(self.assignments.get(volunteer, [])), volunteer.interested_tasks.index(task), id(volunteer), volunteer) for volunteer in interested_volunteers]
                    heapify(interested_heap)

                    # Get the least burdened, highest interested volunteer
                    workload, _, _, chosen_volunteer = heappop(interested_heap)

                else:
                    # Get the least burdened volunteer overall
                    workload, _, chosen_volunteer = heappop(volunteer_heap)

                # Assign the task
                self.assign_task(task, chosen_volunteer)

                # Update heap with the new workload
                heappush(volunteer_heap, (workload + 1, id(chosen_volunteer), chosen_volunteer))

            # Calculate the new volunteer satisfaction score
            num_tasks = len(self.tasks)
            satisfaction_score = get_volunteer_satisfaction_score(self.assignments, self.volunteers, num_tasks)
            print(f"New Volunteer Satisfaction Score: {satisfaction_score}")
        except Exception as e:
            print(f"Error assigning tasks: {e}")
