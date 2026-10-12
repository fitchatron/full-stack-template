"""seed auth tables

Revision ID: 068cf2966dab
Revises: 99c6fff2812f
Create Date: 2026-10-25 17:27:11.586326

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '068cf2966dab'
down_revision: Union[str, Sequence[str], None] = '99c6fff2812f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    insert_permissions = sa.text("""
      INSERT INTO public.permissions (
        action
        ,resource
        ,description
        ,created_by
        ,modified_by
        )
      VALUES (
        '*'
        ,'*'
        ,'Full access to all actions and resources.'
        ,NULL
        ,NULL
        )
        ,(
        '*'
        ,'users'
        ,'Full CRUD access to users.'
        ,NULL
        ,NULL
        )
        ,(
        'read'
        ,'*'
        ,'Full read access to all entities in the app.'
        ,NULL
        ,NULL
        )
        ,(
        '*'
        ,'user_roles'
        ,'Full CRUD access to user roles.'
        ,NULL
        ,NULL
        )
        ,(
        'create'
        ,'users'
        ,'Permission to create users.'
        ,NULL
        ,NULL
        )
        ,(
        'read'
        ,'users'
        ,'Permission to read users.'
        ,NULL
        ,NULL
        )
        ,(
        'update'
        ,'users'
        ,'Permission to update users.'
        ,NULL
        ,NULL
        )
        ,(
        'delete'
        ,'users'
        ,'Permission to delete users.'
        ,NULL
        ,NULL
        )
        ,(
        'create'
        ,'permissions'
        ,'Permission to create permissions.'
        ,NULL
        ,NULL
        )
        ,(
        'read'
        ,'permissions'
        ,'Permission to read permissions.'
        ,NULL
        ,NULL
        )
        ,(
        'update'
        ,'permissions'
        ,'Permission to update permissions.'
        ,NULL
        ,NULL
        )
        ,(
        'delete'
        ,'permissions'
        ,'Permission to delete permissions.'
        ,NULL
        ,NULL
        )
        ,(
        'create'
        ,'roles'
        ,'Permission to create roles.'
        ,NULL
        ,NULL
        )
        ,(
        'read'
        ,'roles'
        ,'Permission to read roles.'
        ,NULL
        ,NULL
        )
        ,(
        'update'
        ,'roles'
        ,'Permission to update roles.'
        ,NULL
        ,NULL
        )
        ,(
        'delete'
        ,'roles'
        ,'Permission to delete roles.'
        ,NULL
        ,NULL
        )
        ,(
        'create'
        ,'role_permissions'
        ,'Permission to create role_permissions.'
        ,NULL
        ,NULL
        )
        ,(
        'read'
        ,'role_permissions'
        ,'Permission to read role_permissions.'
        ,NULL
        ,NULL
        )
        ,(
        'update'
        ,'role_permissions'
        ,'Permission to update role_permissions.'
        ,NULL
        ,NULL
        )
        ,(
        'delete'
        ,'role_permissions'
        ,'Permission to delete role_permissions.'
        ,NULL
        ,NULL
        )
        ,(
        'create'
        ,'user_roles'
        ,'Permission to create user_roles.'
        ,NULL
        ,NULL
        )
        ,(
        'read'
        ,'user_roles'
        ,'Permission to read user_roles.'
        ,NULL
        ,NULL
        )
        ,(
        'update'
        ,'user_roles'
        ,'Permission to update user_roles.'
        ,NULL
        ,NULL
        )
        ,(
        'delete'
        ,'user_roles'
        ,'Permission to delete user_roles.'
        ,NULL
        ,NULL
        );
    """)
    op.execute(insert_permissions)

    insert_roles = sa.text("""
      INSERT INTO public.roles (
        role_id
        ,name
        ,description
        ,created_by
        ,modified_by
        )
      VALUES (
        'admin'
        ,'Admin'
        ,'Administrator role'
        ,NULL
        ,NULL
        )
        ,(
        'user_admin'
        ,'User Admin'
        ,'User Administrator role'
        ,NULL
        ,NULL
        )
        ,(
        'public'
        ,'Public'
        ,'Default public role'
        ,NULL
        ,NULL
        );
    """)
    op.execute(insert_roles)

    insert_admin_role_permissions = sa.text("""
      INSERT INTO public.role_permissions (
        permission_id
        ,role_id
        )
      SELECT permission_id
        ,'admin' AS role_id
      FROM public.permissions
      WHERE action = '*'
        AND resource = '*';
    """)
    op.execute(insert_admin_role_permissions)
    
    insert_user_admin_role_permissions = sa.text("""
      INSERT INTO public.role_permissions (
        permission_id
        ,role_id
        )
      SELECT permission_id
        ,'user_admin' AS role_id
      FROM public.permissions
      WHERE action = '*'
        AND resource IN (
          'users'
          ,'user_roles'
          );
    """)
    op.execute(insert_user_admin_role_permissions)
    
    insert_public_role_permissions = sa.text("""
      INSERT INTO public.role_permissions (
        permission_id
        ,role_id
        )
      SELECT permission_id
        ,'public' AS role_id
      FROM public.permissions
      WHERE (action = 'read' AND resource = 'users')
        OR ( action = 'update' AND resource = 'users')
        OR (action = 'read' AND resource = 'user_roles');
    """)
    op.execute(insert_public_role_permissions)


def downgrade() -> None:
    """Downgrade schema."""
    
    delete_public_role_permissions = sa.text("""
      DELETE
      FROM public.role_permissions
      WHERE role_id = 'public'
        AND permission_id IN (
          SELECT permission_id
          FROM public.permissions
          WHERE (action = 'read' AND resource = 'users')
            OR ( action = 'update' AND resource = 'users')
            OR (action = 'read' AND resource = 'user_roles')
        );
    """)
    op.execute(delete_public_role_permissions)
    
    delete_user_admin_role_permissions = sa.text("""
      DELETE
      FROM role_permissions
      WHERE 1 = 1
        AND role_id = 'user_admin'
        AND permission_id IN (
          SELECT permission_id
          FROM permissions
          WHERE action = '*'
            AND resource IN (
              'users'
              ,'user_roles'
              )
        );
    """)
    op.execute(delete_user_admin_role_permissions)

    delete_admin_role_permissions = sa.text("""
      DELETE
      FROM role_permissions
      WHERE 1 = 1
        AND role_id = 'admin'
        AND permission_id IN (
          SELECT permission_id
          FROM permissions
          WHERE action = '*'
            AND resource = '*'
        );
    """)
    op.execute(delete_admin_role_permissions)
    
    delete_roles = sa.text("""
      DELETE
      FROM public.roles
      WHERE role_id IN ('admin', 'user_admin', 'public');
    """)
    op.execute(delete_roles)
    
    delete_permissions = sa.text("""
      DELETE 
      FROM public.permissions
      WHERE (action, resource) IN (
        ('*', '*'),
        ('*', 'users'),
        ('*', 'user_roles'),
        ('read', '*'),
        ('create', 'users'),
        ('read', 'users'),
        ('update', 'users'),
        ('delete', 'users'),
        ('create', 'permissions'),
        ('read', 'permissions'),
        ('update', 'permissions'),
        ('delete', 'permissions'),
        ('create', 'roles'),
        ('read', 'roles'),
        ('update', 'roles'),
        ('delete', 'roles'),
        ('create', 'role_permissions'),
        ('read', 'role_permissions'),
        ('update', 'role_permissions'),
        ('delete', 'role_permissions'),
        ('create', 'user_roles'),
        ('read', 'user_roles'),
        ('update', 'user_roles'),
        ('delete', 'user_roles')
      );
    """)
    op.execute(delete_permissions)
