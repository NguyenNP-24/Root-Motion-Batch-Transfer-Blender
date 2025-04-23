# Root-Motion-Batch-Transfer
An easy-to-use Blender addon for batch transferring root motion from any rig controller. Supports multiple actions, with root motion either staying static at world origin or following a selected target controller. Ideal for game-ready animations and an efficient workflow. 
Compatible with Blender 4.3.2 and earlier versions.
Workflow:
1. Select Rig (Amature)
2. Go to pose mode and Select all controllers that will control the entire character with the same behavior as the Root controller (in most cases 2 IK leg, 2 IK hand and torso (COG)), select more if your rig has more limbs
3. Click Add Controller button, to add them to Add-on lists
4. Define which is Root controller, and which is target (usually it is Torso, you can choose whatever you want root to follow)
5. Click Tranfer to Root button for currently action. Batch Tranfer to Root for all action from rig. (Keep in world origin toggle enable if you want Root controller reset back to world origin 0,0,0)

UI panel viewport:

![image](https://github.com/user-attachments/assets/81794a75-6d2d-47d8-b35d-bbd23423840c)

illustration of root motion before and after using addon:
![BeforeTool](https://github.com/user-attachments/assets/56a7a969-a53d-44db-aed3-7c37cad0d1f8)
![AfterTool](https://github.com/user-attachments/assets/d2ebd382-3bab-4f4f-ae78-fd5e9eec0659)

Detail add-on tutorial: https://www.youtube.com/watch?v=djH-Jw-y6ag
