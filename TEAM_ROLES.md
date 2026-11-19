# Team BlindSpot Roles

Each teammate owns one deliverable and one peer review this week.

| Teammate | Ownership | Deliverable |
| --- | --- | --- |
| Sapnil Basnet | Web app and integration | Verify PNG and JPEG upload, protan and deutan selection, severity, comparison, and PNG download on the demo machine. Check keyboard access and fix issues that block the workflow. |
| Shivendra Bhagat | Color engine | Establish the protan and deutan baseline on development images. Investigate missed pairs and changes outside targeted regions. Make and test any focused fix that the baseline warrants. |
| Corbin Copper | Accuracy evaluation and demo | Prepare held-out photos, charts, and maps with target regions and answer keys. Run the final evaluation, tabulate results by profile and image type, and prepare the three-image demo. Record before-and-after answer accuracy if participants are available. |

## Work sequence

1. Agree on the scoring threshold, severity, and image questions at kickoff. Set aside the evaluation images before engine tuning.
2. Work in parallel on separate branches in this repo. Keep each pull request focused on its deliverable.
3. Sapnil reviews Shivendra's engine pull request, Shivendra reviews Corbin's evaluation, and Corbin reviews Sapnil's web workflow.
4. Before submission, merge the reviewed changes, rerun the accuracy checks, and rehearse the full workflow from a fresh checkout on the demo machine.
